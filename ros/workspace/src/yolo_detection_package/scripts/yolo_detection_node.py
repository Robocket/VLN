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
from sklearn.cluster import KMeans
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from yolo_detection_package.msg import ObjectDetection, ObjectDetections
from yolo_detection_package.msg import ObjectCoordinate, ObjectCoordinates
from scipy.spatial.transform import Rotation as R
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker, MarkerArray

# 添加YOLOv5本地仓库路径
YOLOV5_REPO_PATH = "/home/crl/yolov5"
sys.path.append(YOLOV5_REPO_PATH)

# 导入YOLOv5本地推理所需模块
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes, check_img_size
from utils.torch_utils import select_device
from utils.augmentations import letterbox

class YOLOv5ROSNode:
    def __init__(self):
        # ROS节点初始化
        rospy.init_node('yolo_detection_node', anonymous=True)
        
        # 常量定义
        self.FRAME_ID = "camera_frame"
        self.CAMERA_INIT_FRAME = "camera_init"  # 目标坐标系
        self.IMAGE_ENCODING = "bgr8"
        self.RETRY_COUNT = 3
        self.RATE_HZ = 15
        self.CONF_THRESH = rospy.get_param('~confidence_threshold', 0.5)
        self.IOU_THRESH = 0.5

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
        self.image_pub = rospy.Publisher('/yolo_detection_result', Image, queue_size=1)
        self.detection_pub = rospy.Publisher('/object_detections', ObjectDetections, queue_size=1)
        self.object_abs_coords_pub = rospy.Publisher( 
            '/object/absolute_coords_list',  # 物体坐标话题名
            ObjectCoordinates,               # 自定义消息类型
            queue_size=1
        )
        # Marker发布者（用于RVIZ可视化）
        self.marker_pub = rospy.Publisher('/object/markers', MarkerArray, queue_size=1)

        # 历史坐标列表（存储多帧数据）
        self.object_coords_list = []
        
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
            queue_size=1
        )

        # ===== 定义旋转矩阵 =====
        self.rot_matrix = np.array([
                                    [0, 0, 1],
                                    [-1, 0, 0],
                                    [0, -1, 0]
                                ], dtype=np.float32)

        # ========== YOLO模型加载 ==========
        self.load_yolo_model()
        self.r_list = ['laptop', 'bottle', 'chair', 'backpack', 'cup', 'mouse', 'keyboard', 'cell phone', 'book', 'scissors', ]    #限制输出的识别结果

    def load_yolo_model(self):
        """加载YOLOv5模型"""
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
            
            self.imgsz = check_img_size((640, 480), s=self.stride)
            
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

    def create_object_markers(self, object_coords_list, header):
        """
        将物体坐标列表转换为RVIZ MarkerArray（每个物体一个点+文字标签）
        """
        marker_array = MarkerArray()
        marker_id = 0  # 每个Marker需要唯一ID
        
        for obj_coord in object_coords_list:
            # 1. 创建点Marker（显示3D坐标点）
            point_marker = Marker()
            point_marker.header = header
            point_marker.ns = "object_points"
            point_marker.id = marker_id
            point_marker.type = Marker.SPHERE
            point_marker.action = Marker.ADD
            # 设置点的位置
            point_marker.pose.position.x = obj_coord.point.x
            point_marker.pose.position.y = obj_coord.point.y
            point_marker.pose.position.z = obj_coord.point.z
            # 设置点的姿态（无旋转）
            point_marker.pose.orientation.x = 0.0
            point_marker.pose.orientation.y = 0.0
            point_marker.pose.orientation.z = 0.0
            point_marker.pose.orientation.w = 1.0
            # 设置点的大小
            point_marker.scale.x = 0.1  # 球体直径0.1m
            point_marker.scale.y = 0.1
            point_marker.scale.z = 0.1
            # 设置颜色（不同类别用不同颜色）
            color_map = {
                "laptop": (1.0, 0.0, 0.0),    # 红色
                "bottle": (0.0, 1.0, 0.0),    # 绿色
                "chair": (0.0, 0.0, 1.0),     # 蓝色
                "default": (1.0, 1.0, 0.0)    # 黄色（默认）
            }
            r, g, b = color_map.get(obj_coord.class_name, color_map["default"])
            point_marker.color.r = r
            point_marker.color.g = g
            point_marker.color.b = b
            point_marker.color.a = 1.0  # 不透明度
            # 设置生命周期（0表示永久，直到被清除）
            point_marker.lifetime = rospy.Duration(0.05)  # 0.05秒后消失（避免残留）
            marker_array.markers.append(point_marker)
            marker_id += 1
            
            # 2. 创建文字标签Marker（显示类别名）
            text_marker = Marker()
            text_marker.header = header
            text_marker.ns = "object_labels"
            text_marker.id = marker_id
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            # 文字位置（在点的上方0.1m处）
            text_marker.pose.position.x = obj_coord.point.x
            text_marker.pose.position.y = obj_coord.point.y
            text_marker.pose.position.z = obj_coord.point.z + 0.1
            # 文字姿态
            text_marker.pose.orientation.w = 1.0
            # 文字内容和大小
            text_marker.text = obj_coord.class_name
            text_marker.scale.z = 0.3  # 文字大小
            # 文字颜色（和点一致）
            text_marker.color.r = r
            text_marker.color.g = g
            text_marker.color.b = b
            text_marker.color.a = 1.0
            text_marker.lifetime = rospy.Duration(0.5)
            marker_array.markers.append(text_marker)
            marker_id += 1
        
        return marker_array
    
    def quaternion_to_rotation_matrix(self, q):
        """将四元数(x,y,z,w)转换为3×3旋转矩阵"""
        quat = [q.x, q.y, q.z, q.w]  # scipy要求(x,y,z,w)顺序
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
    
    def judge_cls(self, cls_name):
        """
        修复：判断该类别是否已存在于历史坐标列表中
        返回值：(has_history, cls_exist)
        - has_history: 是否有历史数据（bool）
        - cls_exist: 该类别是否在历史数据中（bool）
        """
        cls_exist = False
        idx = -1
        # 遍历历史坐标对象，检查class_name属性
        if self.object_coords_list:
            # 遍历历史坐标对象，检查class_name属性
            for i, obj_coord in enumerate(self.object_coords_list):
                if obj_coord.class_name == cls_name:
                    idx = i
                    cls_exist = True
                    break
        
        return idx, cls_exist
        

    def draw_detections_with_features(self, frame, detections, depth_image, object_coords_list):
        """绘制检测结果（显示绝对坐标）"""
        frame_draw = frame.copy()
        valid_depth_values = []
        h, w = frame_draw.shape[:2]  # 获取图像尺寸，用于坐标边界检查
        
        for det in detections:
            x1, y1, x2, y2 = det["xyxy"]
            cls_name = det["class_name"]
            conf = det["conf"]
            
            # ========== 第一步：强制转换坐标为整数，避免浮点型错误 ==========
            x1_int = int(round(x1))
            y1_int = int(round(y1))
            x2_int = int(round(x2))
            y2_int = int(round(y2))
            
            # 边界检查：确保坐标在图像范围内
            x1_int = max(0, min(x1_int, w-1))
            y1_int = max(0, min(y1_int, h-1))
            x2_int = max(0, min(x2_int, w-1))
            y2_int = max(0, min(y2_int, h-1))
            
            # 接收两个返回值
            cls_idx, cls_exist = self.judge_cls(cls_name)
            
            # ========== 核心修复：初始化变量，避免未赋值引用 ==========
            depth_label = "Depth: N/A"  # 初始值
            color = (255, 0, 0)         # 初始颜色（红色）
            
            
            # 绘制检测框（用整数坐标）
            cv2.rectangle(frame_draw, (x1_int, y1_int), (x2_int, y2_int), (0, 0, 255), 2)
            cluster_x = int((x1_int+x2_int)/2) # 聚类中心像素坐标
            cluster_y = int((y1_int+y2_int)/2) 
            target_depth = depth_image.get_distance(cluster_x, cluster_y)
            
            # 绘制中心（紫色圆点）
            if cluster_x > 0 and cluster_y > 0:
                cv2.circle(frame_draw, (cluster_x, cluster_y), 5, (255, 0, 255), -1)
            
            # 绘制深度信息（仅显示聚类中心深度值）
            if target_depth > 0:
                valid_depth_values.append(target_depth)
                depth_label = f"Depth: {target_depth}m"
                color = (0, 255, 255)  # 黄色
                
                # ========== 计算并发布绝对坐标 ==========
                if cluster_x > 0 and cluster_y > 0:
                    relative_z = target_depth
                    relative_x = (cluster_x - self.ppx) * target_depth/self.fx
                    relative_y = (cluster_y - self.ppy) * target_depth/self.fy
                    
                    # 计算绝对坐标
                    abs_coord = self.calculate_absolute_coordinate(relative_x, relative_y, relative_z)
                    if abs_coord is not None:
                        # 构建并发布绝对坐标消息
                        obj_coord = ObjectCoordinate()
                        obj_coord.class_name = cls_name
                        obj_coord.point.x = abs_coord[0]
                        obj_coord.point.y = abs_coord[1]
                        obj_coord.point.z = abs_coord[2]
                        object_coords_list.append(obj_coord)
                        
                        # ========== 绝对坐标文字的坐标强制转int + 边界检查 ==========
                        abs_text_y = y1_int - 50
                        abs_text_y = max(20, abs_text_y)  # 避免文字超出图像顶部
                        abs_label = f"Abs: ({abs_coord[0]:.2f}, {abs_coord[1]:.2f}, {abs_coord[2]:.2f})m"
                        cv2.putText(frame_draw, abs_label, (x1_int, abs_text_y), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                        # 更新历史坐标列表
                        if cls_exist:
                            # 更新已有类别的坐标
                            self.object_coords_list[cls_idx] = obj_coord
                        else:
                            # 更新历史列表，发布
                            self.object_coords_list.append(obj_coord)
                else:
                    rospy.logwarn(f"目标{cls_name}中心无效，跳过坐标计算")
            else:
                depth_label = "Depth: N/A"
                color = (255, 0, 0)  # 红色（无有效深度）
            
            # ========== 第二步：depth_label的坐标，边界检查 ==========
            depth_text_y = y1_int - 30
            depth_text_y = max(15, depth_text_y)  # 避免文字超出图像顶部
            cv2.putText(frame_draw, depth_label, (x1_int, depth_text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # ========== 第三步：类别+置信度的坐标，强制转int + 边界检查 ==========
            label_text_y = y1_int - 10
            label_text_y = max(10, label_text_y)  # 避免文字超出图像顶部
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(frame_draw, label, (x1_int, label_text_y), 
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

    def publish_detected_image(self, frame, detections, header, depth_image, object_coords_list):
        """发布检测图像"""
        try:
            detected_image, valid_depth_count = self.draw_detections_with_features(frame, detections, depth_image, object_coords_list)
            
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
                    
                    # 初始化空列表存储所有物体的类别+坐标
                    object_coords_list = []

                    # 发布检测消息
                    detection_msg = self.build_detection_msg(detections)
                    self.detection_pub.publish(detection_msg)

                    # 发布检测图像（同时收集坐标）
                    self.publish_detected_image(frame, detections, detection_msg.header, depth_frame, object_coords_list)
                    
                    # 构建并发布批量坐标消息
                    if self.object_coords_list:  # 仅当有有效坐标时发布
                        coords_msg = ObjectCoordinates()
                        coords_msg.header = detection_msg.header
                        coords_msg.header.frame_id = self.CAMERA_INIT_FRAME
                        coords_msg.objects = self.object_coords_list  # 赋值坐标列表
                        self.object_abs_coords_pub.publish(coords_msg)
                        # rospy.loginfo(f"发布 {len(self.history_coords_list)} 个物体的绝对坐标列表")
                        
                        # 生成并发布Marker（用于RVIZ可视化）
                        marker_array = self.create_object_markers(self.object_coords_list, coords_msg.header)
                        self.marker_pub.publish(marker_array)
                        # rospy.loginfo(f"发布 {len(marker_array.markers)} 个Marker用于RVIZ可视化")

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