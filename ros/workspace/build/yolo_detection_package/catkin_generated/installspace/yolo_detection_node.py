#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLOv5 ROS Node for RealSense/USB Camera Object Detection
最终版：结合YOLO检测深度 + 位姿变换，发布物体在camera_init的绝对坐标
"""
import cv2
import torch
import numpy as np
import pyrealsense2 as rs
import rospy
import sys
import os
from sklearn.cluster import KMeans
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from yolo_detection_package.msg import ObjectDetection, ObjectDetections
from scipy.spatial.transform import Rotation as R
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PointStamped, Point

# 添加YOLOv5本地仓库路径
YOLOV5_REPO_PATH = "/home/crl/yolov5"
sys.path.append(YOLOV5_REPO_PATH)

# 导入YOLOv5本地推理所需模块
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes, check_img_size
from utils.torch_utils import select_device
from utils.augmentations import letterbox

# 修复amp弃用警告
try:
    from torch.amp import autocast
except ImportError:
    from torch.cuda.amp import autocast

class YOLOv5ROSNode:
    def __init__(self):
        # ROS节点初始化
        rospy.init_node('yolo_detection_node', anonymous=True)
        
        # 常量定义
        self.FRAME_ID = "camera_frame"
        self.CAMERA_INIT_FRAME = "camera_init"  # 新增：目标坐标系
        self.IMAGE_ENCODING = "bgr8"
        self.RETRY_COUNT = 3
        self.RATE_HZ = 15
        self.CONF_THRESH = rospy.get_param('~confidence_threshold', 0.5)
        self.IOU_THRESH = 0.5
        
        # ORB参数（保证足够特征点用于聚类）
        self.orb_nfeatures = rospy.get_param('~orb_nfeatures', 200)
        self.orb_scaleFactor = rospy.get_param('~orb_scaleFactor', 1.2)
        self.orb_edgeThreshold = rospy.get_param('~orb_edgeThreshold', 15)
        self.orb_patchSize = rospy.get_param('~orb_patchSize', 31)
        
        # 初始化ORB检测器（保留，用于提取特征点计算聚类中心）
        self.orb = cv2.ORB_create(
            nfeatures=self.orb_nfeatures,
            scaleFactor=self.orb_scaleFactor,
            edgeThreshold=self.orb_edgeThreshold,
            patchSize=self.orb_patchSize,
            fastThreshold=15
        )

        # RealSense配置
        self.WIDTH = 640
        self.HEIGHT = 480
        self.FPS = 15
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, self.WIDTH, self.HEIGHT, rs.format.bgr8, self.FPS)
        self.config.enable_stream(rs.stream.depth, self.WIDTH, self.HEIGHT, rs.format.z16, self.FPS)
        self.align = rs.align(rs.stream.color)
        self.pipeline_started = False
        # 深度相机内参：
        self.fx = 385.45  # 相机x方向焦距
        self.fy = 385.45  # 相机y方向焦距
        self.ppx = 320.0  # 主点x坐标
        self.ppy = 240.0  # 主点y坐标
        
        # ROS发布者
        self.image_pub = rospy.Publisher('/yolo_detection_result', Image, queue_size=10)
        self.detection_pub = rospy.Publisher('/object_detections', ObjectDetections, queue_size=10)
        self.object_abs_coord_pub = rospy.Publisher( 
            '/object/absolute_coords',
            PointStamped,
            queue_size=10
        )
        
        # 工具初始化
        self.cv_bridge = CvBridge()
        self.rate = rospy.Rate(self.RATE_HZ)
        
        # 存储最新的位姿变换数据（旋转矩阵+平移向量）
        self.latest_R = None
        self.latest_t = None
                
        # 订阅位姿话题（替换为你实际的话题名）
        self.odom_sub = rospy.Subscriber(
            "/Odometry",  # 替换为实际位姿话题名
            Odometry,
            self.odom_callback,
            queue_size=10
        )

        # ===== 定义旋转矩阵 =====
        self.rot_matrix = np.array([
                                    [0, 0, 1],
                                    [1, 0, 0],
                                    [0, -1, 0]
                                ], dtype=np.float32)

        # ========== 修复：YOLO模型加载移到__init__（原代码错误写在odom_callback里） ==========
        self.load_yolo_model()
        self.r_list = ['laptop', 'bottle', 'chair']    #限制输出的识别结果

    def load_yolo_model(self):
        """加载YOLOv5模型（独立函数，修复原代码结构错误）"""
        try:
            self.device = select_device('cpu')
            rospy.loginfo(f"使用设备: {self.device}")
            
            self.weights_path = '/home/crl/yolov5/weights_download/yolov5s.pt'
            
            self.model = DetectMultiBackend(
                self.weights_path, 
                device=self.device, 
                dnn=False,
                fp16=False
            )
            self.stride = self.model.stride
            self.names = self.model.names
            
            self.imgsz = check_img_size((480, 480), s=self.stride)
            
            # 模型预热
            warmup_img = torch.zeros((1, 3, self.imgsz[0], self.imgsz[1]), device=self.device)
            with torch.no_grad():
                self.model(warmup_img)
            
            self.conf_thres = self.CONF_THRESH
            self.iou_thres = self.IOU_THRESH
            rospy.loginfo("YOLOv5模型加载并预热成功！")
        except Exception as e:
            rospy.logfatal(f"模型加载失败: {e}")
            import traceback
            rospy.logfatal(f"详细错误栈: {traceback.format_exc()}")
            raise

    def quaternion_to_rotation_matrix(self, q):
        """将四元数(x,y,z,w)转换为3×3旋转矩阵"""
        quat = [q.w, q.x, q.y, q.z]  # scipy要求(w,x,y,z)顺序
        rot = R.from_quat(quat)
        return rot.as_matrix()
    
    def odom_callback(self, msg):
        """位姿回调：存储最新的旋转矩阵和平移向量（不再直接计算，移到检测逻辑中）"""
        try:
            # 1. 提取body坐标系原点在camera_init的平移向量t
            self.latest_t = np.array([
                [msg.pose.pose.position.x],
                [msg.pose.pose.position.y],
                [msg.pose.pose.position.z]
            ])

            # 2. 四元数转旋转矩阵R（body→camera_init的旋转）
            self.latest_R = self.quaternion_to_rotation_matrix(msg.pose.pose.orientation)

            rospy.logdebug("已更新最新的位姿变换矩阵")

        except Exception as e:
            rospy.logerr(f"位姿解析出错：{str(e)}")

    def calculate_absolute_coordinate(self, relative_x, relative_y, relative_z):
        """
        核心：根据最新位姿，计算物体绝对坐标
        :param relative_x/y/z: 物体相对body坐标系的坐标（从YOLO检测获取）
        :return: 绝对坐标(x,y,z) 或 None（位姿未更新）
        """
        if self.latest_R is None or self.latest_t is None:
            rospy.logwarn("位姿数据未更新，无法计算绝对坐标！")
            return None
        
        # 原始坐标
        original_p = np.array([relative_x, relative_y, relative_z], dtype=np.float32).reshape(3,1)
        # 左乘旋转矩阵得到变换后坐标
        transformed_p = np.dot(self.rot_matrix, original_p)
        # 构建相对坐标列向量
        P_body = transformed_p.reshape(3,1)
        
        # 刚体变换计算绝对坐标
        P_camera = self.latest_R @ P_body + self.latest_t
        
        return (P_camera[0,0], P_camera[1,0], P_camera[2,0])

    def preprocess_image(self, frame):
        """图像预处理"""
        img = letterbox(frame, self.imgsz, stride=self.stride, auto=False)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = np.ascontiguousarray(img, dtype=np.float32)
        img /= 255.0
        
        img = torch.from_numpy(img).to(self.device, non_blocking=True)
        if len(img.shape) == 3:
            img = img.unsqueeze(0)
        
        return img, frame.shape[:2]

    def postprocess_results(self, pred, orig_shape):
        """推理结果后处理"""
        pred = non_max_suppression(
            pred, 
            self.conf_thres, 
            self.iou_thres, 
            classes=None, 
            agnostic=True,
            max_det=10
        )
        
        detections = []
        for det in pred:
            if len(det):
                det[:, :4] = scale_boxes(self.imgsz, det[:, :4], orig_shape).round()
                confs = det[:, 4].cpu().numpy()
                clss = det[:, 5].cpu().numpy().astype(int)
                xyxy = det[:, :4].cpu().numpy()
                
                for i in range(len(det)):
                    if self.names[clss[i]] in self.r_list:
                        detections.append({
                            "xyxy": xyxy[i],
                            "conf": confs[i],
                            "cls": clss[i],
                            "class_name": self.names[clss[i]]
                        })
        return detections
    
    def get_orb_keypoints(self, frame, box):
        """提取检测框内的ORB特征点（仅用于计算聚类中心，不显示）"""
        x1, y1, x2, y2 = box
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # 边界检查
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1]-1, x2)
        y2 = min(frame.shape[0]-1, y2)
        
        # 提取检测框区域
        box_region = frame[y1:y2, x1:x2]
        if box_region.size == 0:
            return []
        
        # 检测ORB特征点
        gray_box = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
        kp_box, des_box = self.orb.detectAndCompute(gray_box, None)
        
        # 转换特征点坐标到全局坐标系
        for p in kp_box:
            p.pt = (p.pt[0] + x1, p.pt[1] + y1)
        
        return kp_box
    
    def calculate_target_depth_kmeans(self, kp_list, depth_image):
        """
        使用K-means聚类特征点计算目标深度（仅取聚类中心深度）
        核心逻辑：
        1. 对特征点坐标做K-means聚类（k=1）找到中心位置
        2. 取中心位置的深度值作为目标深度（仅过滤0值）
        """
        # 至少需要5个特征点才进行聚类
        if len(kp_list) < 5:
            return 0.0, (0, 0)
        
        # 提取特征点坐标
        pts = np.array([[p.pt[0], p.pt[1]] for p in kp_list], dtype=np.float32)
        
        # K-means聚类（k=1）找特征点中心
        try:
            kmeans = KMeans(n_clusters=1, random_state=0, n_init=5)
            kmeans.fit(pts)
            center = kmeans.cluster_centers_[0]  # 聚类中心坐标
            center_x = int(round(center[0]))
            center_y = int(round(center[1]))
        except Exception as e:
            rospy.logwarn(f"K-means聚类失败: {e}")
            return 0.0, (0, 0)
        
        # 获取中心位置的深度值（仅过滤0值）
        depth_value = depth_image.get_distance(center_x, center_y)
        if depth_value <= 0:
            return 0.0, (center_x, center_y)
        
        # 转换为米并保留3位小数
        depth_m = round(depth_value, 3)
        
        return depth_m, (center_x, center_y)
    
    def draw_detections_with_features(self, frame, detections, depth_image):
        """绘制检测结果（显示绝对坐标）"""
        frame_draw = frame.copy()
        valid_depth_values = []
        
        for det in detections:
            x1, y1, x2, y2 = det["xyxy"]
            cls_name = det["class_name"]
            conf = det["conf"]
            
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # box_center_x = (x1 + x2) / 2
            # box_center_y = (y1 + y2) / 2
            # # 使用检测框深度）
            # center_depth = depth_image.get_distance(box_center_x, box_center_y)

            # 绘制检测框
            cv2.rectangle(frame_draw, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # 提取ORB特征点（仅用于计算聚类中心，不显示）
            kp_list = self.get_orb_keypoints(frame, (x1, y1, x2, y2))
            
            # 使用K-means计算目标深度（取聚类中心深度）
            target_depth, center_pt = self.calculate_target_depth_kmeans(kp_list, depth_image)
            cluster_x, cluster_y = center_pt  # 聚类中心像素坐标

            # 绘制聚类中心（紫色圆点）
            if center_pt[0] > 0 and center_pt[1] > 0:
                cv2.circle(frame_draw, center_pt, 5, (255, 0, 255), -1)
            
            # 绘制深度信息（仅显示聚类中心深度值）
            if target_depth > 0:
                valid_depth_values.append(target_depth)
                depth_label = f"Depth: {target_depth}m"
                color = (0, 255, 255)  # 黄色
                
                # ========== 计算并发布绝对坐标 ==========
                # 假设检测框中心的像素坐标转换为相对body的x/y（示例：像素→米的简单映射，需根据相机内参调整）
                if cluster_x > 0 and cluster_y > 0:
                    relative_x = (self.ppx - cluster_x) * target_depth/self.fx  # 中心偏移转为相对x
                    relative_y = (self.ppy - cluster_y) * target_depth/self.fy # 中心偏移转为相对y
                    relative_z = np.sqrt(target_depth**2 - relative_x**2 - relative_y**2)
                    # rospy.loginfo(
                    #     f"目标:{cls_name}\n"
                    #     f"聚类中心像素: ({cluster_x}, {cluster_y})\n"
                    #     f"位置:X:{relative_x}, Y:{relative_y}, Z:{relative_z}\n"
                    #     f"距离:{target_depth}"
                    #               )
                    
                    # 计算绝对坐标
                    abs_coord = self.calculate_absolute_coordinate(relative_x, relative_y, relative_z)
                    if abs_coord is not None:
                        # 构建并发布绝对坐标消息
                        abs_point_msg = PointStamped()
                        abs_point_msg.header.stamp = rospy.get_rostime()
                        abs_point_msg.header.frame_id = self.CAMERA_INIT_FRAME
                        abs_point_msg.point.x = abs_coord[0]
                        abs_point_msg.point.y = abs_coord[1]
                        abs_point_msg.point.z = abs_coord[2]
                        self.object_abs_coord_pub.publish(abs_point_msg)
                        
                        # 绘制绝对坐标到图像
                        abs_label = f"Abs: ({abs_coord[0]:.2f}, {abs_coord[1]:.2f}, {abs_coord[2]:.2f})m"
                        cv2.putText(frame_draw, abs_label, (x1, y1-50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                else:
                    rospy.logwarn(f"目标{cls_name}聚类中心无效，跳过坐标计算")
            else:
                depth_label = "Depth: N/A"
                color = (255, 0, 0)  # 红色（无有效深度）
            
            cv2.putText(frame_draw, depth_label, (x1, y1-30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 绘制类别+置信度
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(frame_draw, label, (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame_draw, len(valid_depth_values)
    
    def build_detection_msg(self, detections):
        """构建检测消息"""
        detection_msg = ObjectDetections()
        detection_msg.header.stamp = rospy.get_rostime()
        detection_msg.header.frame_id = self.FRAME_ID
        
        for det in detections:
            obj = ObjectDetection()
            x1, y1, x2, y2 = det["xyxy"]
            obj.class_name = det["class_name"]
            obj.x_center = (x1 + x2) / 2
            obj.y_center = (y1 + y2) / 2
            obj.width = x2 - x1
            obj.height = y2 - y1
            obj.confidence = det["conf"]
            detection_msg.objects.append(obj)
        
        return detection_msg

    def publish_detected_image(self, frame, detections, header, depth_image):
        """发布检测图像"""
        try:
            detected_image, valid_depth_count = self.draw_detections_with_features(frame, detections, depth_image)
            rospy.logdebug(f"发布图像 - 检测到 {len(detections)} 个目标, {valid_depth_count} 个有效深度")
            
            img_msg = self.cv_bridge.cv2_to_imgmsg(detected_image, self.IMAGE_ENCODING)
            img_msg.header = header
            self.image_pub.publish(img_msg)
        except CvBridgeError as e:
            rospy.logerr(f"图像转换错误: {e}")
        except Exception as e:
            rospy.logerr(f"图像渲染/发布错误: {e}")

    def run_realsense(self):
        """运行RealSense摄像头处理"""
        # 启动RealSense pipeline
        retry = 0
        while retry < self.RETRY_COUNT and not rospy.is_shutdown():
            try:
                self.pipeline.start(self.config)
                self.pipeline_started = True
                rospy.loginfo("RealSense摄像头（彩色+深度流）启动成功！")
                break
            except RuntimeError as e:
                retry += 1
                rospy.logerr(f"RealSense启动失败（重试{retry}/{self.RETRY_COUNT}）：{e}")
                rospy.sleep(1)
        
        if not self.pipeline_started:
            rospy.logfatal("RealSense启动重试次数耗尽，程序退出！")
            return
        
        try:
            while not rospy.is_shutdown():
                try:
                    start_time = rospy.get_time()
                    
                    frames = self.pipeline.wait_for_frames(timeout_ms=2000)
                    if not frames:
                        rospy.logwarn("未获取到帧，跳过本次循环")
                        self.rate.sleep()
                        continue
                    
                    # 对齐深度帧
                    aligned_frames = self.align.process(frames)
                    color_frame = aligned_frames.get_color_frame()
                    depth_frame = aligned_frames.get_depth_frame()
                    if not color_frame or not depth_frame:
                        rospy.logwarn("彩色帧/深度帧读取失败！")
                        self.rate.sleep()
                        continue

                    # 转换为numpy数组
                    frame = np.asanyarray(color_frame.get_data(), dtype=np.uint8)
                    
                    # YOLO推理
                    img, orig_shape = self.preprocess_image(frame)
                    with torch.no_grad():
                        pred = self.model(img, augment=False, visualize=False)
                    
                    # 结果后处理
                    detections = self.postprocess_results(pred, orig_shape)
                    
                    # 发布消息
                    detection_msg = self.build_detection_msg(detections)
                    self.detection_pub.publish(detection_msg)
                    self.publish_detected_image(frame, detections, detection_msg.header, depth_frame)
                    
                    # 打印帧率
                    elapsed_time = rospy.get_time() - start_time
                    rospy.logdebug(f"单帧耗时: {elapsed_time:.3f}s, 帧率: {1/elapsed_time:.1f}FPS")
                    
                    self.rate.sleep()

                except Exception as e:
                    rospy.logerr(f"帧处理异常: {e}")
                    self.rate.sleep()
                    continue
        finally:
            self.cleanup()

    def cleanup(self):
        """资源释放（修复原代码中self.cap未定义的问题）"""
        rospy.loginfo("开始释放资源...")
        if self.pipeline_started:
            try:
                self.pipeline.stop()
                rospy.loginfo("RealSense pipeline已停止")
            except Exception as e:
                rospy.logerr(f"停止RealSense失败: {e}")
        cv2.destroyAllWindows()
        rospy.loginfo("资源释放完成")

if __name__ == '__main__':
    node = None
    try:
        node = YOLOv5ROSNode()
        node.run_realsense()
        # node.run_usb_camera()
    except rospy.ROSInterruptException:
        rospy.loginfo("ROS节点被用户中断")
    except Exception as e:
        rospy.logfatal(f"节点运行异常: {str(e)}")
        import traceback
        rospy.logfatal(f"详细错误栈: {traceback.format_exc()}")
    finally:
        if node:
            node.cleanup()
