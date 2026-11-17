"""Proactive OneStreamer responses label synchronized camera-visible point clouds."""

import base64
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
import json
import queue
import signal
import threading

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from visualization_msgs.msg import Marker, MarkerArray
from vln_interfaces.msg import ObjectCoordinate, ObjectCoordinates

from .projection import (
    DEFAULT_TASK, GROUNDING_FORMAT, parse_regions, project_visible, rotation_matrix, semantic_records,
)
from .streamer import DEFAULT_ROOT, DEFAULT_SOCKET, SocketClient, StreamerSettings, WorkerProcess


def stamp_ns(stamp):
    return stamp.sec * 1_000_000_000 + stamp.nanosec


@dataclass
class Snapshot:
    header: Header
    cloud_stamp_ns: int
    pose_stamp_ns: int | None
    image: np.ndarray
    points: np.ndarray
    uv: np.ndarray
    depth: np.ndarray
    frame_id: str


class SemanticNode(Node):
    def __init__(self, settings=None, client=None, **kwargs):
        super().__init__('streaming_semantic_node', **kwargs)
        self.declare_parameters('', [
            ('robot_agent_root', DEFAULT_ROOT), ('onestreamer_config', 'configs/onestreamer-fast.json'),
            ('worker_python', ''), ('model_path', ''), ('grounding_max_new_tokens', 256),
            ('socket_path', DEFAULT_SOCKET), ('start_worker', True), ('startup_timeout', 120.0),
            ('color_topic', '/camera/color/image_raw'), ('camera_info_topic', '/camera/color/camera_info'),
            ('cloud_topic', '/cloud_registered'), ('odom_topic', '/Odometry'), ('frame_id', 'world'),
            ('transform_mode', 'odometry'), ('sync_tolerance', 0.15),
            ('fx', 385.45), ('fy', 385.45), ('cx', 320.0), ('cy', 240.0),
            ('image_width', 640), ('image_height', 480), ('image_rectified', False),
            ('camera_to_body_rotation', [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
            ('camera_to_body_translation', [0.0, 0.0, 0.0]),
            ('near_clip', 0.05), ('far_clip', 30.0), ('visibility_cell_size', 2),
            ('occlusion_tolerance', 0.1), ('foreground_depth_band', 0.3), ('min_region_points', 3),
            ('task', DEFAULT_TASK), ('task_topic', '/semantic/task'),
        ])
        self._validate()
        self.settings = settings or StreamerSettings.load(
            *[self.param(k) for k in ('robot_agent_root', 'onestreamer_config', 'worker_python',
                                      'model_path', 'grounding_max_new_tokens')])
        self.process = None
        self.client = client or SocketClient(self.param('socket_path'), self.settings.timeout,
                                             self.param('startup_timeout'))
        self.bridge = CvBridge()
        self.clouds, self.odoms = deque(maxlen=32), deque(maxlen=128)
        self.camera_info = None
        self.window = []
        self.busy = self.closed = False
        self.generation = 0
        self.last_seen = self.last_sampled = self.accept_after = None
        self.task = self.param('task')
        self.results = queue.SimpleQueue()
        self.label_ids = {}
        self.thread = None
        self.tf_buffer = self.tf_listener = None
        if self.param('transform_mode') == 'tf':
            from tf2_ros import Buffer, TransformListener
            self.tf_buffer = Buffer(node=self)
            self.tf_listener = TransformListener(self.tf_buffer, self)
        self.cloud_pub = self.create_publisher(PointCloud2, '/semantic/cloud', 1)
        self.labels_pub = self.create_publisher(String, '/semantic/labels', 1)
        self.state_pub = self.create_publisher(String, '/semantic/state', 10)
        self.image_pub = self.create_publisher(Image, '/semantic/projection', 1)
        self.coords_pub = self.create_publisher(ObjectCoordinates, '/object/absolute_coords_list', 1)
        self.marker_pub = self.create_publisher(MarkerArray, '/object/markers', 1)
        self.create_subscription(PointCloud2, self.param('cloud_topic'), lambda msg: self.clouds.append(msg),
                                 qos_profile_sensor_data)
        self.create_subscription(Odometry, self.param('odom_topic'), lambda msg: self.odoms.append(msg),
                                 qos_profile_sensor_data)
        self.create_subscription(CameraInfo, self.param('camera_info_topic'), self.on_camera_info,
                                 qos_profile_sensor_data)
        self.create_subscription(Image, self.param('color_topic'), self.on_image, qos_profile_sensor_data)
        self.create_subscription(String, self.param('task_topic'), self.on_task, 10)
        self.create_timer(0.05, self.poll_results)
        if self.param('start_worker'):
            try:
                self.process = WorkerProcess(self.settings, self.param('socket_path'))
            except Exception:
                self.client.close()
                super().destroy_node()
                raise
        self.get_logger().info(
            f'OneStreamer: {self.settings.sample_fps:g} fps, four-frame batches; '
            'semantic annotation only on grounded Response events')

    def param(self, key):
        return self.get_parameter(key).value

    def _validate(self):
        for key in ('fx', 'fy', 'sync_tolerance', 'startup_timeout', 'foreground_depth_band'):
            if not np.isfinite(self.param(key)) or self.param(key) <= 0:
                raise ValueError(f'{key} must be finite and positive')
        if self.param('transform_mode') not in ('tf', 'odometry'):
            raise ValueError('transform_mode must be tf or odometry')
        if (not all(np.isfinite(self.param(k)) for k in ('near_clip', 'far_clip', 'occlusion_tolerance'))
                or not 0 < self.param('near_clip') < self.param('far_clip')
                or self.param('occlusion_tolerance') < 0):
            raise ValueError('Invalid projection depth limits')
        if not self.param('task').strip() or len(self.param('task')) > 4096:
            raise ValueError('task must contain between 1 and 4096 characters')
        if min(self.param(k) for k in ('image_width', 'image_height', 'visibility_cell_size', 'min_region_points')) < 1:
            raise ValueError('Image sizes, visibility cells and min_region_points must be positive')
        rotation = np.array(self.param('camera_to_body_rotation')).reshape(3, 3)
        translation = np.array(self.param('camera_to_body_translation'))
        if (not np.isfinite(rotation).all() or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6)
                or not np.isclose(np.linalg.det(rotation), 1.0) or translation.shape != (3,)
                or not np.isfinite(translation).all()):
            raise ValueError('Camera extrinsics must define a finite rigid transform')

    def on_camera_info(self, msg):
        if msg.k[0] > 0 and msg.k[4] > 0:
            self.camera_info = msg

    def on_task(self, msg):
        task = msg.data.strip()
        if not task or len(task) > 4096:
            self.get_logger().warning('Empty or oversized semantic task ignored')
            return
        self.task = task
        self.generation += 1
        self.window.clear()
        self.last_sampled = None

    def nearest(self, messages, timestamp):
        if not messages:
            raise ValueError('Waiting for synchronized point cloud / odometry')
        msg = min(messages, key=lambda m: abs(stamp_ns(m.header.stamp) - timestamp))
        if abs(stamp_ns(msg.header.stamp) - timestamp) > self.param('sync_tolerance') * 1e9:
            raise ValueError('Point cloud / odometry is outside sync_tolerance')
        return msg

    def snapshot(self, msg):
        timestamp = stamp_ns(msg.header.stamp)
        cloud = self.nearest(self.clouds, timestamp)
        if cloud.header.frame_id != self.param('frame_id'):
            raise ValueError(f'Cloud frame {cloud.header.frame_id!r} differs from frame_id')
        image = self.bridge.imgmsg_to_cv2(msg, 'bgr8').copy()
        height, width = image.shape[:2]
        info = self.camera_info
        rectification = None
        if info is not None:
            if info.header.frame_id != msg.header.frame_id or (info.width, info.height) != (width, height):
                raise ValueError('CameraInfo must match the color image frame and resolution')
            if self.param('image_rectified'):
                projection = np.array(info.p).reshape(3, 4)
                if not np.allclose(projection[:, 3], 0.0):
                    raise ValueError('Rectified stereo baselines are not supported; use the monocular camera')
                k = projection[:, :3]
                rectification = np.array(info.r).reshape(3, 3)
                if (not np.isfinite(rectification).all()
                        or not np.allclose(rectification.T @ rectification, np.eye(3), atol=1e-6)
                        or not np.isclose(np.linalg.det(rectification), 1.0)):
                    raise ValueError('CameraInfo.R must be a valid rectification rotation')
                distortion, model = np.zeros(5), ''
            else:
                k = np.array(info.k).reshape(3, 3)
                distortion, model = np.array(info.d), info.distortion_model
        else:
            if (width, height) != (self.param('image_width'), self.param('image_height')):
                raise ValueError('Fallback intrinsics require the configured image resolution')
            k = np.array([[self.param('fx'), 0.0, self.param('cx')],
                          [0.0, self.param('fy'), self.param('cy')], [0.0, 0.0, 1.0]])
            distortion, model = np.zeros(5), ''
        if k[0, 0] <= 0 or k[1, 1] <= 0 or not np.isfinite(k).all():
            raise ValueError('Invalid camera calibration')
        # Keep the input untouched: the sensor_msgs helper may byte-swap a big-endian buffer.
        if cloud.is_bigendian:
            cloud = deepcopy(cloud)
        points = point_cloud2.read_points_numpy(cloud, field_names=['x', 'y', 'z'], skip_nans=True).reshape(-1, 3)
        pose_stamp = None
        if self.tf_buffer is not None:
            transform = self.tf_buffer.lookup_transform(msg.header.frame_id, cloud.header.frame_id,
                                                        Time.from_msg(msg.header.stamp)).transform
            rotation = rotation_matrix(transform.rotation)
            t = transform.translation
            camera_points = points @ rotation.T + [t.x, t.y, t.z]
        else:
            odom = self.nearest(self.odoms, timestamp)
            if odom.header.frame_id != cloud.header.frame_id:
                raise ValueError('Odometry and cloud must use the same world frame')
            rotation = rotation_matrix(odom.pose.pose.orientation)
            p = odom.pose.pose.position
            body = (points - [p.x, p.y, p.z]) @ rotation
            camera_rotation = np.array(self.param('camera_to_body_rotation')).reshape(3, 3)
            camera_points = (body - self.param('camera_to_body_translation')) @ camera_rotation
            pose_stamp = stamp_ns(odom.header.stamp)
        if rectification is not None:
            camera_points = camera_points @ rectification.T
        points, uv, depth = project_visible(
            points, camera_points, image, k, distortion, model, self.param('near_clip'),
            self.param('far_clip'), self.param('visibility_cell_size'), self.param('occlusion_tolerance'))
        if not len(points):
            raise ValueError('No visible point cloud samples in the camera frustum')
        return Snapshot(deepcopy(msg.header), stamp_ns(cloud.header.stamp), pose_stamp,
                        image, points, uv, depth, cloud.header.frame_id)

    def on_image(self, msg):
        timestamp = stamp_ns(msg.header.stamp)
        if self.last_seen is not None and timestamp < self.last_seen:
            self.generation += 1
            self.window.clear()
            self.last_sampled = self.accept_after = None
            # Drop samples from the previous clock epoch before reusing the sync caches.
            for messages in (self.clouds, self.odoms):
                kept = [x for x in messages if stamp_ns(x.header.stamp) <= timestamp]
                messages.clear()
                messages.extend(kept)
        self.last_seen = timestamp
        if self.busy or (self.accept_after is not None and timestamp <= self.accept_after):
            return
        if self.last_sampled is not None and timestamp - self.last_sampled < 1e9 / self.settings.sample_fps:
            return
        try:
            snapshot = self.snapshot(msg)
            ok, jpeg = cv2.imencode('.jpg', snapshot.image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                raise ValueError('JPEG encoding failed')
        except Exception as exc:
            self.get_logger().warning(f'Frame skipped: {exc}', throttle_duration_sec=5.0)
            return
        self.last_sampled = timestamp
        self.window.append((snapshot, base64.b64encode(jpeg).decode('ascii')))
        if len(self.window) != 4:
            return
        batch, self.window = self.window, []
        generation = self.generation
        request = {'question': self.task, 'grounding_prompt': GROUNDING_FORMAT, 'version': generation,
                   'sample_fps': self.settings.sample_fps,
                   'frames': [{'stamp_ns': stamp_ns(item.header.stamp), 'jpeg': jpeg} for item, jpeg in batch]}
        self.busy = True

        def run():
            try:
                result = self.client.infer(request)
            except Exception as exc:
                result = {'ok': False, 'error': str(exc)}
            self.results.put((generation, request, batch[-1][0], result))

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def poll_results(self):
        if self.process is not None and self.process.process.poll() is not None:
            raise RuntimeError(f'OneStreamer worker exited: {self.process.process.returncode}')
        while not self.results.empty():
            generation, request, snapshot, result = self.results.get()
            self.busy = False
            self.accept_after = self.last_seen
            state = {k: value for k, value in result.items() if k != 'keyframes'}
            state.update(generation=generation, source_cloud_ns=snapshot.cloud_stamp_ns)
            try:
                if generation != self.generation:
                    state['discarded'] = 'task or source clock changed during inference'
                elif not result.get('ok'):
                    raise ValueError(result.get('error', 'OneStreamer failed'))
                elif (result.get('source_end_ns') != stamp_ns(snapshot.header.stamp)
                      or result.get('source_start_ns') != request['frames'][0]['stamp_ns']
                      or result.get('question') != request['question']):
                    raise ValueError('OneStreamer result does not match the captured frame window')
                elif result.get('response') is not None:
                    regions = parse_regions(result['response'])
                    self.annotate(snapshot, regions, generation)
                    state['annotation_regions'] = len(regions)
            except Exception as exc:
                state['annotation_error'] = str(exc)
                self.get_logger().error(f'Semantic annotation rejected: {exc}')
            self.state_pub.publish(String(data=json.dumps(state, ensure_ascii=False)))

    def annotate(self, snapshot, regions, generation):
        image = snapshot.image.copy()
        height, width = image.shape[:2]
        records, annotations = semantic_records(
            snapshot, regions, self.label_ids,
            self.param('foreground_depth_band'), self.param('min_region_points'))
        header = deepcopy(snapshot.header)
        header.frame_id = snapshot.frame_id
        fields = [PointField(name=name, offset=i*4, datatype=(PointField.FLOAT32 if i < 3 else PointField.UINT32),
                             count=1) for i, name in enumerate(records.dtype.names)]
        cloud = PointCloud2(header=header, height=1, width=len(records), fields=fields, is_bigendian=False,
                            point_step=24, row_step=len(records)*24, data=records.tobytes(), is_dense=True)
        coords = ObjectCoordinates(header=deepcopy(header))
        markers = MarkerArray(markers=[Marker(action=Marker.DELETEALL)])
        for index, item in enumerate(annotations):
            obj = ObjectCoordinate(class_name=item['label'])
            obj.point.x, obj.point.y, obj.point.z = item['centroid']
            coords.objects.append(obj)
            marker = Marker(header=header, ns='semantic_objects', id=index, type=Marker.TEXT_VIEW_FACING,
                            action=Marker.ADD, text=item['label'])
            marker.pose.position = deepcopy(obj.point)
            marker.pose.position.z += 0.2
            marker.pose.orientation.w = 1.0
            marker.scale.z = 0.2
            marker.color.r = marker.color.g = marker.color.b = marker.color.a = 1.0
            markers.markers.append(marker)
            box = np.array(item['bbox']) * [width/1000, height/1000, width/1000, height/1000]
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(image, item['label'], (x1, max(12, y1-4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        for (u, v), color in zip(snapshot.uv, records['rgb']):
            color = int(color)
            image[v, u] = [color & 255, (color >> 8) & 255, (color >> 16) & 255]
        preview = self.bridge.cv2_to_imgmsg(image, 'bgr8')
        preview.header = deepcopy(snapshot.header)
        legend = {'stamp_ns': stamp_ns(snapshot.header.stamp), 'frame_id': snapshot.frame_id,
                  'image_frame_id': snapshot.header.frame_id, 'source_cloud_ns': snapshot.cloud_stamp_ns,
                  'source_pose_ns': snapshot.pose_stamp_ns, 'generation': generation,
                  'labels': {'0': 'unlabeled', **{str(value): key for key, value in self.label_ids.items()}},
                  'regions': annotations, 'method': 'vlm_box_depth_band_weak_labels',
                  'visible_points': len(records), 'labeled_points': int(np.count_nonzero(records['label_id']))}
        self.cloud_pub.publish(cloud)
        self.labels_pub.publish(String(data=json.dumps(legend, ensure_ascii=False)))
        self.coords_pub.publish(coords)
        self.marker_pub.publish(markers)
        self.image_pub.publish(preview)

    def destroy_node(self):
        self.closed = True
        self.client.close()
        if self.thread is not None:
            self.thread.join(timeout=1)
        if self.process is not None:
            self.process.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SemanticNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
