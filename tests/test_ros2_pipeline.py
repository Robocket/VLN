"""Real DDS and Unix-socket pipeline; only the GPU worker is scripted."""

import json
import os
from pathlib import Path as FilePath
import signal
import socketserver
import subprocess
import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest
import rclpy
from ament_index_python.packages import get_package_prefix
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image, PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from vln_interfaces.msg import ObjectCoordinates
from vln_navigation.goal_selector import GoalSelector
from vln_perception.semantic_node import SemanticNode


class ScriptedWorker:
    def __init__(self, path):
        self.response = json.dumps({'objects': [{'label': 'bottle', 'bbox': [200, 200, 800, 800]}]})
        self.offset = 0
        self.gate = threading.Event()
        self.gate.set()
        self.requests = []
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                while line := self.rfile.readline():
                    item = json.loads(line)
                    owner.requests.append(item)
                    owner.gate.wait(timeout=5)
                    response = owner.response
                    result = {'ok': True, 'question': item['question'], 'response': response,
                              'raw': '</Response>' + response if response is not None else '</Silence>',
                              'source_start_ns': item['frames'][0]['stamp_ns'],
                              'source_end_ns': item['frames'][-1]['stamp_ns'] + owner.offset}
                    self.wfile.write(json.dumps(result).encode() + b'\n')
                    self.wfile.flush()

        self.server = socketserver.UnixStreamServer(path, Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.gate.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)


@pytest.fixture
def graph(tmp_path, request):
    rclpy.init()
    executor = SingleThreadedExecutor()
    harness = Node('vln_test_harness')
    socket_path = str(tmp_path / 's.sock')
    worker = ScriptedWorker(socket_path)
    settings = SimpleNamespace(sample_fps=20.0, timeout=3.0)
    semantic = SemanticNode(settings=settings, parameter_overrides=[
        Parameter('transform_mode', value=getattr(request, 'param', 'odometry')),
        Parameter('start_worker', value=False), Parameter('socket_path', value=socket_path),
        Parameter('fx', value=4.0), Parameter('fy', value=4.0),
        Parameter('cx', value=4.0), Parameter('cy', value=4.0),
        Parameter('image_width', value=8), Parameter('image_height', value=8)])
    selector = GoalSelector()
    nodes = [harness, semantic, selector]
    for node in nodes:
        executor.add_node(node)
    received = {key: [] for key in ('coords', 'clouds', 'states', 'labels', 'goals', 'paths')}
    subscriptions = [harness.create_subscription(cls, topic, received[key].append, 10)
                     for cls, topic, key in [
                         (ObjectCoordinates, '/object/absolute_coords_list', 'coords'),
                         (PointCloud2, '/semantic/cloud', 'clouds'), (String, '/semantic/state', 'states'),
                         (String, '/semantic/labels', 'labels'), (PoseStamped, '/vln_goal', 'goals'),
                         (Path, '/planned_path', 'paths')]]
    publishers = {
        'color': harness.create_publisher(Image, '/camera/color/image_raw', qos_profile_sensor_data),
        'odom': harness.create_publisher(Odometry, '/Odometry', qos_profile_sensor_data),
        'cloud': harness.create_publisher(PointCloud2, '/cloud_registered', qos_profile_sensor_data),
        'instruction': harness.create_publisher(String, '/vln/instruction', 10),
        'task': harness.create_publisher(String, '/semantic/task', 10),
        'goal': harness.create_publisher(PoseStamped, '/vln_goal', 10),
    }

    def wait(predicate, timeout=6.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.02)
            if predicate():
                return
        assert predicate(), 'Timed out waiting for ROS graph'

    def pump(seconds=0.15):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.01)

    def frame(distance=2.0, cloud_frame='world', wall=False, at=None):
        stamp = harness.get_clock().now().to_msg() if at is None else Time(nanoseconds=at).to_msg()
        header = Header(stamp=stamp, frame_id=cloud_frame)
        points = [(distance, -0.1, -0.1), (distance, 0.1, -0.1), (distance, 0.0, 0.1)]
        if wall:
            points += [(1.0, float(y), 1.5) for y in np.arange(-0.5, 0.6, 0.1)]
        publishers['cloud'].publish(point_cloud2.create_cloud_xyz32(header, points))
        odom = Odometry(header=Header(stamp=stamp, frame_id='world'))
        odom.pose.pose.orientation.w = 1.0
        publishers['odom'].publish(odom)
        pump(0.02)
        color = CvBridge().cv2_to_imgmsg(np.zeros((8, 8, 3), dtype=np.uint8), 'bgr8')
        color.header = Header(stamp=stamp, frame_id='camera_color_optical_frame')
        publishers['color'].publish(color)
        pump(0.07)
        return stamp.sec * 1_000_000_000 + stamp.nanosec

    def batch(**kwargs):
        stamp = None
        for _ in range(4):
            stamp = frame(**kwargs)
        return stamp

    wait(lambda: publishers['color'].get_subscription_count() >= 1
         and publishers['cloud'].get_subscription_count() >= 1
         and publishers['odom'].get_subscription_count() >= 2
         and publishers['instruction'].get_subscription_count() >= 1)
    try:
        yield harness, semantic, worker, received, publishers, wait, pump, frame, batch
    finally:
        worker.gate.set()
        for node in nodes:
            executor.remove_node(node)
            node.destroy_node()
        worker.close()
        subscriptions.clear()
        executor.shutdown()
        rclpy.shutdown()


def test_response_labels_camera_visible_cloud_and_preserves_world_coordinates(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    last = batch()
    wait(lambda: bool(received['clouds']) and bool(received['coords']) and bool(received['labels']))
    cloud = received['clouds'][-1]
    assert cloud.header.frame_id == 'world'
    assert cloud.header.stamp.sec * 1_000_000_000 + cloud.header.stamp.nanosec == last
    points = point_cloud2.read_points(cloud)
    assert len(points) == 3
    assert set(points['label_id']) == {1}
    assert set(points['instance_id']) == {1}
    assert received['coords'][-1].objects[0].class_name == 'bottle'
    assert received['coords'][-1].objects[0].point.x == pytest.approx(2.0)
    legend = json.loads(received['labels'][-1].data)
    assert legend['labeled_points'] == 3
    assert legend['labels'] == {'0': 'unlabeled', '1': 'bottle'}
    assert len(worker.requests) == 1 and len(worker.requests[0]['frames']) == 4


def test_silence_and_invalid_grounding_do_not_publish_labels(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    worker.response = None
    batch()
    wait(lambda: len(received['states']) == 1)
    assert not received['clouds'] and not received['coords']
    worker.response = 'A bottle is visible, somewhere.'
    batch()
    wait(lambda: len(received['states']) == 2)
    assert 'annotation_error' in json.loads(received['states'][-1].data)
    assert not received['clouds'] and not received['coords']


def test_delayed_response_uses_captured_cloud_not_latest_cloud(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    worker.gate.clear()
    stamp = batch()
    wait(lambda: bool(worker.requests))
    frame(distance=3.0)
    worker.gate.set()
    wait(lambda: bool(received['coords']) and bool(received['clouds']))
    assert received['coords'][-1].objects[0].point.x == pytest.approx(2.0)
    header = received['clouds'][-1].header
    assert header.stamp.sec * 1_000_000_000 + header.stamp.nanosec == stamp


def test_wrong_result_timestamp_and_input_frame_are_rejected(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    batch(cloud_frame='unrelated_frame')
    assert not worker.requests
    worker.offset = 1
    batch()
    wait(lambda: bool(received['states']))
    assert 'does not match' in json.loads(received['states'][-1].data)['annotation_error']
    assert not received['coords'] and not received['clouds']


def test_task_change_discards_inflight_result(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    worker.gate.clear()
    batch()
    wait(lambda: bool(worker.requests))
    pubs['task'].publish(String(data='Report only chairs entering the view.'))
    pump()
    worker.gate.set()
    wait(lambda: bool(received['states']))
    assert 'discarded' in json.loads(received['states'][-1].data)
    assert not received['coords']


def test_rectified_camera_info_applies_its_rotation_before_projection(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    semantic.set_parameters([Parameter('image_rectified', value=True)])
    info = CameraInfo(header=Header(frame_id='camera_color_optical_frame'), width=8, height=8,
                      k=[4.0, 0.0, 4.0, 0.0, 4.0, 4.0, 0.0, 0.0, 1.0],
                      r=[0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                      p=[4.0, 0.0, 4.0, 0.0, 0.0, 4.0, 4.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    semantic.on_camera_info(info)
    frame()
    assert len(semantic.window) == 1
    np.testing.assert_array_equal(semantic.window[0][0].uv, [[4, 3], [4, 4], [3, 4]])


@pytest.mark.parametrize('graph', ['tf'], indirect=True)
def test_calibrated_tf_projects_points_in_the_image_optical_frame(graph):
    from tf2_ros import StaticTransformBroadcaster
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    broadcaster = StaticTransformBroadcaster(harness)
    transform = TransformStamped(header=Header(frame_id='world'), child_frame_id='camera_color_optical_frame')
    transform.transform.rotation.x = transform.transform.rotation.y = 0.5
    transform.transform.rotation.z = transform.transform.rotation.w = 0.5
    broadcaster.sendTransform(transform)
    wait(lambda: semantic.tf_buffer.can_transform('camera_color_optical_frame', 'world', Time()))
    batch()
    wait(lambda: bool(received['coords']))
    assert received['coords'][-1].objects[0].point.x == pytest.approx(2.0)


def test_clock_rewind_resets_session_and_keeps_sensor_subscriptions_working(graph):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    batch()
    wait(lambda: len(received['clouds']) == 1)
    for i in range(4):
        frame(distance=3.0, at=1_000_000_000 + i * 100_000_000)
    wait(lambda: len(received['clouds']) == 2)
    assert worker.requests[-1]['version'] > worker.requests[0]['version']
    points = point_cloud2.read_points(received['clouds'][-1])
    assert np.allclose(points['x'], 3.0)


def test_proactive_semantics_to_goal_and_obstacle_avoiding_path(graph, tmp_path):
    harness, semantic, worker, received, pubs, wait, pump, frame, batch = graph
    executable = FilePath(get_package_prefix('vln_planner')) / 'lib/vln_planner/a_star_planner_node'
    with (tmp_path / 'planner.log').open('w') as log:
        process = subprocess.Popen([str(executable), '--ros-args', '-p', 'resolution:=0.1',
                                    '-p', 'grid_width:=80', '-p', 'grid_height:=80'],
                                   stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
        try:
            wait(lambda: pubs['odom'].get_subscription_count() >= 3
                 and pubs['cloud'].get_subscription_count() >= 2
                 and pubs['goal'].get_subscription_count() >= 1)
            pump()
            batch(wall=True)
            wait(lambda: bool(received['coords']))
            pump()
            pubs['instruction'].publish(String(data='bottle'))
            wait(lambda: bool(received['paths']))
            assert process.poll() is None
            path = received['paths'][-1]
            assert path.header.frame_id == 'world'
            assert path.poses[0].pose.position.x == pytest.approx(0.0)
            assert path.poses[-1].pose.position.x == pytest.approx(2.0)
            assert max(abs(p.pose.position.y) for p in path.poses) > 0.6
            received['paths'].clear()
            goal = PoseStamped(header=Header(frame_id='world'))
            goal.pose.position.x = 100.0
            goal.pose.orientation.w = 1.0
            pubs['goal'].publish(goal)
            wait(lambda: bool(received['paths']))
            assert not received['paths'][-1].poses
        finally:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
