"""ROS 2 RGB-D detection and object localization."""

from copy import deepcopy
import signal

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image
from visualization_msgs.msg import Marker, MarkerArray
from vln_interfaces.msg import (
    ObjectCoordinate, ObjectCoordinates, ObjectDetection, ObjectDetections,
)

from .backend import YoloV5Backend


def stamp_seconds(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


def rotation_matrix(q):
    """Normalize the ROS quaternion and return its rotation matrix."""
    v = np.array([q.x, q.y, q.z, q.w], dtype=float)
    norm = np.linalg.norm(v)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError('Invalid odometry quaternion')
    x, y, z, w = v / norm
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ])


class DetectionNode(Node):
    def __init__(self, backend=None, **kwargs):
        super().__init__('yolo_detection_node', **kwargs)
        defaults = {
            'yolov5_repo': '', 'weights_path': '', 'device': 'cpu',
            'confidence_threshold': 0.5, 'iou_threshold': 0.5,
            'color_topic': '/camera/color/image_raw',
            'depth_topic': '/camera/aligned_depth_to_color/image_raw',
            'camera_info_topic': '/camera/color/camera_info',
            'odom_topic': '/Odometry', 'frame_id': 'world',
            'processing_rate': 15.0, 'sync_tolerance': 0.01, 'max_pose_age': 0.2,
            'fx': 385.45, 'fy': 385.45, 'cx': 320.0, 'cy': 240.0,
            # Optical-camera to body convention; configure from sensor calibration.
            'camera_to_body_rotation': [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            'camera_to_body_translation': [0.0, 0.0, 0.0],
            'classes': ['laptop', 'bottle', 'chair', 'backpack', 'cup', 'mouse',
                        'keyboard', 'cell phone', 'book', 'scissors', 'refrigerator'],
        }
        self.declare_parameters('', list(defaults.items()))
        self.frame_id = self.param('frame_id')
        self.camera_rotation = np.array(self.param('camera_to_body_rotation')).reshape(3, 3)
        self.camera_translation = np.array(self.param('camera_to_body_translation'))
        if self.param('processing_rate') <= 0 or min(self.param('fx'), self.param('fy')) <= 0:
            raise ValueError('processing_rate, fx and fy must be positive')
        self.intrinsics = [self.param(k) for k in ('fx', 'fy', 'cx', 'cy')]
        self.classes = set(self.param('classes'))
        self.bridge = CvBridge()
        self.color = self.depth = self.odom = None
        self.last_stamp = None
        self.history = {}
        self.backend = backend if backend is not None else YoloV5Backend(
            *[self.param(k) for k in ('yolov5_repo', 'weights_path', 'device',
                                      'confidence_threshold', 'iou_threshold')])
        self.image_pub = self.create_publisher(Image, '/yolo_detection_result', 1)
        self.detection_pub = self.create_publisher(ObjectDetections, '/object_detections', 1)
        self.coords_pub = self.create_publisher(ObjectCoordinates, '/object/absolute_coords_list', 1)
        self.marker_pub = self.create_publisher(MarkerArray, '/object/markers', 1)
        self.create_subscription(Image, self.param('color_topic'), self.on_color, qos_profile_sensor_data)
        self.create_subscription(Image, self.param('depth_topic'), self.on_depth, qos_profile_sensor_data)
        self.create_subscription(CameraInfo, self.param('camera_info_topic'), self.on_camera_info,
                                 qos_profile_sensor_data)
        self.create_subscription(Odometry, self.param('odom_topic'), self.on_odom, qos_profile_sensor_data)
        self.create_timer(1.0 / self.param('processing_rate'), self.process_frame)
        self.get_logger().info('Waiting for synchronized color, aligned depth and odometry')

    def param(self, name):
        return self.get_parameter(name).value

    def on_color(self, msg):
        self.color = msg

    def on_depth(self, msg):
        self.depth = msg

    def on_odom(self, msg):
        self.odom = msg

    def on_camera_info(self, msg):
        if msg.k[0] > 0 and msg.k[4] > 0:
            self.intrinsics = [msg.k[0], msg.k[4], msg.k[2], msg.k[5]]

    def process_frame(self):
        if self.color is None or self.depth is None:
            return
        color, depth = self.color, self.depth
        stamp = stamp_seconds(color.header.stamp)
        if stamp == self.last_stamp:
            return
        if abs(stamp - stamp_seconds(depth.header.stamp)) > self.param('sync_tolerance'):
            return
        self.last_stamp = stamp
        try:
            frame = self.bridge.imgmsg_to_cv2(color, 'bgr8')
            depth_img = self.bridge.imgmsg_to_cv2(depth, 'passthrough')
            if depth.encoding not in ('16UC1', '32FC1') or depth_img.shape != frame.shape[:2]:
                raise ValueError('Depth must be aligned to color, with encoding 16UC1 or 32FC1')
            scale = 0.001 if depth.encoding == '16UC1' else 1.0
            detections = self.backend.detect(frame)
            msg = ObjectDetections(header=deepcopy(color.header))
            drawing = frame.copy()
            pose_valid = (self.odom is not None and self.odom.header.frame_id == self.frame_id
                          and abs(stamp - stamp_seconds(self.odom.header.stamp))
                          <= self.param('max_pose_age'))
            if pose_valid:
                rotation = rotation_matrix(self.odom.pose.pose.orientation)
                p = self.odom.pose.pose.position
                translation = np.array([p.x, p.y, p.z])
            fx, fy, cx, cy = self.intrinsics
            height, width = frame.shape[:2]
            for name, confidence, box in detections:
                if name not in self.classes:
                    continue
                x1, y1, x2, y2 = map(float, box)
                u, v = int((x1+x2)/2), int((y1+y2)/2)
                msg.objects.append(ObjectDetection(
                    class_name=name, confidence=float(confidence),
                    x_center=(x1+x2)/2, y_center=(y1+y2)/2, width=x2-x1, height=y2-y1))
                cv2.rectangle(drawing, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                cv2.putText(drawing, f'{name}: {confidence:.2f}', (int(x1), max(15, int(y1)-5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                if not pose_valid or not (0 <= u < width and 0 <= v < height):
                    continue
                distance = float(depth_img[v, u]) * scale
                if not np.isfinite(distance) or distance <= 0:
                    continue
                camera_point = np.array([(u-cx)*distance/fx, (v-cy)*distance/fy, distance])
                absolute = rotation @ (self.camera_rotation @ camera_point
                                       + self.camera_translation) + translation
                obj = ObjectCoordinate(class_name=name)
                obj.point.x, obj.point.y, obj.point.z = map(float, absolute)
                self.history[name] = obj
            self.detection_pub.publish(msg)
            image_msg = self.bridge.cv2_to_imgmsg(drawing, 'bgr8')
            image_msg.header = deepcopy(color.header)
            self.image_pub.publish(image_msg)
            if pose_valid:
                coords = ObjectCoordinates(header=deepcopy(color.header), objects=list(self.history.values()))
                coords.header.frame_id = self.frame_id
                self.coords_pub.publish(coords)
                self.marker_pub.publish(self.markers(coords))
        except Exception as exc:
            self.get_logger().error(f'Frame processing failed: {exc}')

    def markers(self, coords):
        result = MarkerArray()
        for i, obj in enumerate(coords.objects):
            for is_text in (False, True):
                marker = Marker(header=coords.header, ns='object_labels' if is_text else 'object_points',
                                id=i, type=Marker.TEXT_VIEW_FACING if is_text else Marker.SPHERE,
                                action=Marker.ADD)
                marker.pose.position = deepcopy(obj.point)
                marker.pose.orientation.w = 1.0
                marker.scale.x = marker.scale.y = marker.scale.z = 0.1
                marker.color.g = marker.color.a = 1.0
                marker.lifetime = Duration(seconds=0.5).to_msg()
                if is_text:
                    marker.pose.position.z += 0.2
                    marker.text = obj.class_name
                    marker.scale.z = 0.2
                result.markers.append(marker)
        return result


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = DetectionNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
