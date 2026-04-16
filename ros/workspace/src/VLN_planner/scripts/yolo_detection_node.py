import cv2
import torch
import numpy as np
import rospy
import sys
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from VLN_planner.msg import ObjectDetection, ObjectDetections
from VLN_planner.msg import ObjectCoordinate, ObjectCoordinates
from scipy.spatial.transform import Rotation as R
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker, MarkerArray
from threading import Lock

# 添加YOLOv5本地仓库路径
YOLOV5_REPO_PATH = "/home/k325/yolov5"
sys.path.append(YOLOV5_REPO_PATH)

# 导入YOLOv5本地推理所需模块
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes, check_img_size
from utils.torch_utils import select_device
from utils.augmentations import letterbox

class YOLOv5ROSNode:
    def __init__(self):
        # ROS节点初始化
        rospy.init_node('yolo_detection_topic_node', anonymous=True)
        
        # 常量定义
        self.FRAME_ID = "camera_frame"
        self.CAMERA_INIT_FRAME = "camera_init"  # 目标坐标系
        self.IMAGE_ENCODING = "bgr8"
        self.RATE_HZ = 15
        self.CONF_THRESH = rospy.get_param('~confidence_threshold', 0.5)
        self.IOU_THRESH = 0.5

        # ========== 话题订阅配置 ==========
        # 从ROS参数获取要订阅的话题名（运行时可通过参数覆盖）
        self.color_topic = rospy.get_param('~color_topic', "/camera/color/image_raw")
        self.depth_topic = rospy.get_param('~depth_topic', "/camera/depth/image_rect_raw")
        
        # 图像缓存（存储最新的彩色/深度图像，带时间戳用于同步）
        self.latest_color = {"img": None, "stamp": None}
        self.latest_depth = {"img": None, "stamp": None}
        self.img_lock = Lock()     # 线程锁，保证多线程读写安全
        self.TIME_SYNC_THRESH = 0.01  # 时间同步阈值（10ms）
        
        # 深度相机内参（保持不变）
        self.fx = 385.45  # 相机x方向焦距
        self.fy = 385.45  # 相机y方向焦距
        self.ppx = 320.0  # 主点x坐标
        self.ppy = 240.0  # 主点y坐标
        
        # ROS发布者（保持不变）
        self.image_pub = rospy.Publisher('/yolo_detection_result', Image, queue_size=1)
        self.detection_pub = rospy.Publisher('/object_detections', ObjectDetections, queue_size=1)
        self.object_abs_coords_pub = rospy.Publisher( 
            '/object/absolute_coords_list',
            ObjectCoordinates,
            queue_size=1
        )
        self.marker_pub = rospy.Publisher('/object/markers', MarkerArray, queue_size=1)

        # 历史坐标列表
        self.object_history = {}  
        
        # 工具初始化
        self.cv_bridge = CvBridge()
        self.rate = rospy.Rate(self.RATE_HZ)
        
        # 存储最新的位姿变换数据
        self.latest_R = None
        self.latest_t = None
                
        # 订阅位姿话题（保持不变）
        self.odom_sub = rospy.Subscriber(
            "/Odometry",
            Odometry,
            self.odom_callback,
            queue_size=1
        )

        # ========== 订阅彩色/深度图像话题 ==========
        self.color_sub = rospy.Subscriber(
            self.color_topic,
            Image,
            self.color_image_callback,
            queue_size=1  # 只保留最新的1条消息
        )
        
        self.depth_sub = rospy.Subscriber(
            self.depth_topic,
            Image,
            self.depth_image_callback,
            queue_size=1
        )

        # 旋转矩阵（保持不变）
        self.rot_matrix = np.array([
                                    [0, 0, 1],
                                    [-1, 0, 0],
                                    [0, -1, 0]
                                ], dtype=np.float32)

        # 加载YOLO模型（保持不变）
        self.load_yolo_model()
        self.resource_list = ['laptop', 'bottle', 'chair', 'backpack', 'cup', 'mouse', 'keyboard', 'cell phone', 'book', 'scissors', 'refrigerator']

    def load_yolo_model(self):
        """加载YOLOv5模型（保持不变）"""
        try:
            self.device = select_device('cpu')
            rospy.loginfo(f"使用设备: {self.device}")
            
            self.weights_path = '/home/k325/yolov5/weights_download/yolov5s.pt'
            
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

    def create_object_markers(self, object_history_dict, header):
        """创建RVIZ Marker（适配字典版历史坐标，自动适配任意类别）"""
        marker_array = MarkerArray()
        marker_id = 0

        # 遍历字典（key=类别名，value=坐标对象）
        for cls_name, obj_coord in object_history_dict.items():
            # 跳过无效坐标
            if obj_coord is None:
                continue

            # 点Marker
            point_marker = Marker()
            point_marker.header = header
            point_marker.ns = "object_points"
            point_marker.id = marker_id
            point_marker.type = Marker.SPHERE
            point_marker.action = Marker.ADD
            point_marker.pose.position.x = obj_coord.point.x
            point_marker.pose.position.y = obj_coord.point.y
            point_marker.pose.position.z = obj_coord.point.z
            point_marker.pose.orientation.w = 1.0
            point_marker.scale.x = 0.1
            point_marker.scale.y = 0.1
            point_marker.scale.z = 0.1
            color_map = {
                "laptop": (1.0, 0.0, 0.0),
                "bottle": (0.0, 1.0, 0.0),
                "chair": (0.0, 0.0, 1.0),
                "default": (1.0, 1.0, 0.0)
            }
            r, g, b = color_map.get(obj_coord.class_name, color_map["default"])
            point_marker.color.r = r
            point_marker.color.g = g
            point_marker.color.b = b
            point_marker.color.a = 1.0
            point_marker.lifetime = rospy.Duration(0.05)
            marker_array.markers.append(point_marker)
            marker_id += 1

            # 文字标签Marker
            text_marker = Marker()
            text_marker.header = header
            text_marker.ns = "object_labels"
            text_marker.id = marker_id
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = obj_coord.point.x
            text_marker.pose.position.y = obj_coord.point.y
            text_marker.pose.position.z = obj_coord.point.z + 0.1
            text_marker.pose.orientation.w = 1.0
            text_marker.text = obj_coord.class_name
            text_marker.scale.z = 0.3
            text_marker.color.r = r
            text_marker.color.g = g
            text_marker.color.b = b
            text_marker.color.a = 1.0
            text_marker.lifetime = rospy.Duration(0.5)
            marker_array.markers.append(text_marker)
            marker_id += 1

        return marker_array

    def quaternion_to_rotation_matrix(self, q):
        """四元数转旋转矩阵（保持不变）"""
        quat = [q.x, q.y, q.z, q.w]# scipy要求(x,y,z,w)顺序
        rot = R.from_quat(quat)
        return rot.as_matrix()
    
    def odom_callback(self, msg):
        """位姿回调（保持不变）"""
        try:
            self.latest_t = np.array([
                [msg.pose.pose.position.x],
                [msg.pose.pose.position.y],
                [msg.pose.pose.position.z]
            ])
            self.latest_R = self.quaternion_to_rotation_matrix(msg.pose.pose.orientation)
            rospy.logdebug("已更新最新的位姿变换矩阵")
        except Exception as e:
            rospy.logerr(f"位姿解析出错：{str(e)}")

    def calculate_absolute_coordinate(self, relative_x, relative_y, relative_z):
        """计算绝对坐标（保持不变）"""
        if self.latest_R is None or self.latest_t is None:
            rospy.logwarn("位姿数据未更新，无法计算绝对坐标！")
            return None
        
        original_p = np.array([relative_x, relative_y, relative_z], dtype=np.float32).reshape(3,1)
        transformed_p = np.dot(self.rot_matrix, original_p)
        P_body = transformed_p.reshape(3,1)
        
        P_camera = self.latest_R @ P_body + self.latest_t
        
        return (P_camera[0,0], P_camera[1,0], P_camera[2,0])

    def preprocess_image(self, frame):
        """图像预处理（保持不变）"""
        img = letterbox(frame, self.imgsz, stride=self.stride, auto=False)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = np.ascontiguousarray(img, dtype=np.float32)
        img /= 255.0
        
        img = torch.from_numpy(img).to(self.device, non_blocking=True)
        if len(img.shape) == 3:
            img = img.unsqueeze(0)
        
        return img, frame.shape[:2]

    def postprocess_results(self, pred, orig_shape):
        """推理结果后处理（保持不变）"""
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
                    if self.names[clss[i]] in self.resource_list:
                        detections.append({
                            "xyxy": xyxy[i],
                            "conf": confs[i],
                            "cls": clss[i],
                            "class_name": self.names[clss[i]]
                        })
        return detections

    def get_depth_at_pixel(self, depth_img, x, y):
        """获取像素深度值（保持不变）"""
        try:
            # 边界检查
            h, w = depth_img.shape
            if x < 0 or x >= w or y < 0 or y >= h:
                return 0.0
            
            # 获取深度值（mm转m）
            depth_mm = depth_img[y, x]
            if depth_mm == 0:  # 无效深度
                return 0.0
            return depth_mm / 1000.0
        except Exception as e:
            rospy.logerr(f"获取深度值失败: {e}")
            return 0.0

    def draw_detections_with_features(self, frame, detections, depth_img):
        """绘制检测结果（保持不变）"""
        frame_draw = frame.copy()
        valid_depth_values = []
        h, w = frame_draw.shape[:2]
        
        for det in detections:
            x1, y1, x2, y2 = det["xyxy"]
            cls_name = det["class_name"]
            conf = det["conf"]
            
            # 坐标转换和边界检查
            x1_int = int(round(x1))
            y1_int = int(round(y1))
            x2_int = int(round(x2))
            y2_int = int(round(y2))
            
            x1_int = max(0, min(x1_int, w-1))
            y1_int = max(0, min(y1_int, h-1))
            x2_int = max(0, min(x2_int, w-1))
            y2_int = max(0, min(y2_int, h-1))
            
            depth_label = "Depth: N/A"
            color = (255, 0, 0)
            
            # 绘制检测框
            cv2.rectangle(frame_draw, (x1_int, y1_int), (x2_int, y2_int), (0, 0, 255), 2)
            cluster_x = int((x1_int+x2_int)/2)
            cluster_y = int((y1_int+y2_int)/2) 
            
            # 获取深度值
            target_depth = self.get_depth_at_pixel(depth_img, cluster_x, cluster_y)
            
            # 绘制中心
            if cluster_x > 0 and cluster_y > 0:
                cv2.circle(frame_draw, (cluster_x, cluster_y), 5, (255, 0, 255), -1)
            
            # 处理深度值
            if target_depth > 0:
                valid_depth_values.append(target_depth)
                depth_label = f"Depth: {target_depth:.2f}m"
                color = (0, 255, 255)
                
                # 计算相对坐标和绝对坐标
                if cluster_x > 0 and cluster_y > 0:
                    relative_z = target_depth
                    relative_x = (cluster_x - self.ppx) * target_depth/self.fx
                    relative_y = (cluster_y - self.ppy) * target_depth/self.fy
                    
                    abs_coord = self.calculate_absolute_coordinate(relative_x, relative_y, relative_z)
                    if abs_coord is not None:
                        obj_coord = ObjectCoordinate()
                        obj_coord.class_name = cls_name
                        obj_coord.point.x = abs_coord[0]
                        obj_coord.point.y = abs_coord[1]
                        obj_coord.point.z = abs_coord[2]
                        
                        # 绘制绝对坐标
                        abs_text_y = y1_int - 50
                        abs_text_y = max(20, abs_text_y)
                        abs_label = f"Abs: ({abs_coord[0]:.2f}, {abs_coord[1]:.2f}, {abs_coord[2]:.2f})m"
                        cv2.putText(frame_draw, abs_label, (x1_int, abs_text_y), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                        
                        # 更新历史列表
                        self.object_history[cls_name] = obj_coord
                else:
                    rospy.logwarn(f"目标{cls_name}中心无效，跳过坐标计算")
            else:
                depth_label = "Depth: N/A"
                color = (255, 0, 0)
            
            # 绘制深度信息
            depth_text_y = y1_int - 30
            depth_text_y = max(15, depth_text_y)
            cv2.putText(frame_draw, depth_label, (x1_int, depth_text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 绘制类别+置信度
            label_text_y = y1_int - 10
            label_text_y = max(10, label_text_y)
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(frame_draw, label, (x1_int, label_text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame_draw, len(valid_depth_values)

    def build_detection_msg(self, detections):
        """构建检测消息（保持不变）"""
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

    def publish_detected_image(self, frame, detections, header, depth_img):
        """发布检测图像"""
        try:
            detected_image, valid_depth_count = self.draw_detections_with_features(frame, detections, depth_img)
            
            img_msg = self.cv_bridge.cv2_to_imgmsg(detected_image, self.IMAGE_ENCODING)
            img_msg.header = header
            self.image_pub.publish(img_msg)
        except CvBridgeError as e:
            rospy.logerr(f"图像转换错误: {e}")
        except Exception as e:
            rospy.logerr(f"图像渲染/发布错误: {e}")

    # ========== 彩色图像回调函数 ==========
    def color_image_callback(self, msg):
        """接收彩色图像消息并缓存"""
        try:
            with self.img_lock:
                # 将ROS图像消息转为cv2格式
                self.latest_color["img"] = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
                self.latest_color["stamp"] = msg.header.stamp  # 记录时间戳
                self.latest_header = msg.header  # 保存header（用于发布消息）
        except CvBridgeError as e:
            rospy.logerr(f"彩色图像转换失败: {e}")

    # ========== 深度图像回调函数 ==========
    def depth_image_callback(self, msg):
        """接收深度图像消息并缓存"""
        try:
            with self.img_lock:
                # ROS深度图像通常是16位uint，单位mm
                self.latest_depth["img"] = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding="16UC1")
                self.latest_depth["stamp"] = msg.header.stamp  # 记录时间戳
        except CvBridgeError as e:
            rospy.logerr(f"深度图像转换失败: {e}")

    # ========== 主处理循环 ==========
    def run_topic_processing(self):
        """运行话题订阅模式的主处理循环"""
        rospy.loginfo(f"开始订阅话题 - 彩色: {self.color_topic}, 深度: {self.depth_topic}")
        rospy.loginfo("等待图像消息...（可播放rosbag文件）")
        
        while not rospy.is_shutdown():
            try:
                # 检查是否有可用的彩色和深度图像
                with self.img_lock:
                    color_img = self.latest_color["img"]
                    depth_img = self.latest_depth["img"]
                    color_stamp = self.latest_color["stamp"]
                    depth_stamp = self.latest_depth["stamp"]
                    header = self.latest_header
                
                # 1. 检查图像是否有效
                if color_img is None or depth_img is None:
                    self.rate.sleep()
                    continue
                
                # 2. 时间同步检查（确保彩色和深度图像是同一帧）
                if color_stamp is not None and depth_stamp is not None:
                    time_diff = abs((color_stamp - depth_stamp).to_sec())
                    if time_diff > self.TIME_SYNC_THRESH:
                        rospy.logdebug(f"图像时间不同步（差值: {time_diff:.3f}s），跳过")
                        self.rate.sleep()
                        continue
                
                # 3. 执行YOLO检测和坐标计算
                # YOLO推理
                img, orig_shape = self.preprocess_image(color_img)
                with torch.no_grad():
                    pred = self.model(img, augment=False, visualize=False)
                
                # 结果后处理
                detections = self.postprocess_results(pred, orig_shape)
                
                # 发布检测消息
                detection_msg = self.build_detection_msg(detections)
                self.detection_pub.publish(detection_msg)

                # 发布检测图像
                self.publish_detected_image(color_img, detections, header, depth_img)
                
                # 发布绝对坐标和Marker
                stable_coords = list(self.object_history.values())
                if len(stable_coords) > 0:
                # if stable_coords:
                    coords_msg = ObjectCoordinates()
                    coords_msg.header = detection_msg.header
                    coords_msg.header.frame_id = self.CAMERA_INIT_FRAME
                    coords_msg.objects = stable_coords
                    self.object_abs_coords_pub.publish(coords_msg)

                    marker_array = self.create_object_markers(self.object_history, coords_msg.header)
                    self.marker_pub.publish(marker_array)

                # 控制处理速度
                self.rate.sleep()

            except Exception as e:
                rospy.logerr(f"帧处理异常: {e}")
                self.rate.sleep()
                continue

    def cleanup(self):
        """资源释放（保持不变）"""
        rospy.loginfo("开始释放资源...")
        cv2.destroyAllWindows()
        rospy.loginfo("资源释放完成")

if __name__ == '__main__':
    node = None
    try:
        node = YOLOv5ROSNode()
        # 运行话题订阅模式的主循环
        node.run_topic_processing()
    except rospy.ROSInterruptException:
        rospy.loginfo("ROS节点被用户中断")
    except Exception as e:
        rospy.logfatal(f"节点运行异常: {str(e)}")
        import traceback
        rospy.logfatal(f"详细错误栈: {traceback.format_exc()}")
    finally:
        if node:
            node.cleanup()
