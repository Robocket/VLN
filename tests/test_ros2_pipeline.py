"""Exercise real DDS, generated messages and the compiled planner without model weights.

Run after building and sourcing ros2/install/setup.bash.
Only the neural-network backend is replaced by a deterministic detection.
"""

import os
from pathlib import Path as FilePath
import signal
import subprocess
import time

import numpy as np
import pytest
import rclpy
from ament_index_python.packages import get_package_prefix
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from vln_interfaces.msg import ObjectCoordinates, ObjectDetections
from vln_navigation.goal_selector import GoalSelector
from vln_perception.detector import DetectionNode


class Backend:
    def detect(self, frame):
        return [('bottle', 0.9, (2.0, 2.0, 6.0, 6.0))]


@pytest.fixture
def graph():
    rclpy.init()
    executor = SingleThreadedExecutor()
    harness = Node('vln_test_harness')
    detector = DetectionNode(backend=Backend(), parameter_overrides=[
        Parameter('fx', value=100.0), Parameter('fy', value=100.0),
        Parameter('cx', value=4.0), Parameter('cy', value=4.0)])
    selector = GoalSelector()
    nodes = [harness, detector, selector]
    for node in nodes:
        executor.add_node(node)
    received = {key: [] for key in ('coords', 'detections', 'goals', 'paths')}
    subscriptions = [harness.create_subscription(cls, topic, received[key].append, 10)
                     for cls, topic, key in [
                         (ObjectCoordinates, '/object/absolute_coords_list', 'coords'),
                         (ObjectDetections, '/object_detections', 'detections'),
                         (PoseStamped, '/vln_goal', 'goals'), (Path, '/planned_path', 'paths')]]
    publishers = {
        'color': harness.create_publisher(Image, '/camera/color/image_raw', qos_profile_sensor_data),
        'depth': harness.create_publisher(Image, '/camera/aligned_depth_to_color/image_raw', qos_profile_sensor_data),
        'odom': harness.create_publisher(Odometry, '/Odometry', qos_profile_sensor_data),
        'cloud': harness.create_publisher(point_cloud2.PointCloud2, '/cloud_registered', qos_profile_sensor_data),
        'instruction': harness.create_publisher(String, '/vln/instruction', 10),
        'goal': harness.create_publisher(PoseStamped, '/vln_goal', 10),
    }

    def wait(predicate, timeout=6.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.02)
            if predicate():
                return
        assert predicate(), 'Timed out waiting for ROS graph'

    def pump(seconds=0.3):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.02)

    def images(encoding='16UC1', offset=0.0, odom_frame='world'):
        header = Header(stamp=harness.get_clock().now().to_msg(), frame_id='camera_color_optical_frame')
        bridge = CvBridge()
        color = bridge.cv2_to_imgmsg(np.zeros((8, 8, 3), dtype=np.uint8), 'bgr8')
        depth = bridge.cv2_to_imgmsg(
            np.full((8, 8), 2000 if encoding == '16UC1' else 2.0,
                    dtype=np.uint16 if encoding == '16UC1' else np.float32), encoding)
        color.header = header
        depth.header = Header(stamp=header.stamp, frame_id=header.frame_id)
        # Assign a separate stamp so the color header is not mutated.
        depth.header.stamp = rclpy.time.Time(seconds=(header.stamp.sec +
                                                     header.stamp.nanosec * 1e-9 + offset)).to_msg()
        odom = Odometry(header=Header(stamp=header.stamp, frame_id=odom_frame))
        odom.pose.pose.orientation.w = 1.0
        publishers['odom'].publish(odom)
        publishers['depth'].publish(depth)
        publishers['color'].publish(color)

    wait(lambda: publishers['color'].get_subscription_count() >= 1
         and publishers['depth'].get_subscription_count() >= 1
         and publishers['odom'].get_subscription_count() >= 2
         and publishers['instruction'].get_subscription_count() >= 1)
    try:
        yield harness, detector, received, publishers, wait, pump, images
    finally:
        for node in nodes:
            executor.remove_node(node)
            node.destroy_node()
        subscriptions.clear()
        executor.shutdown()
        rclpy.shutdown()


@pytest.mark.parametrize('encoding', ['16UC1', '32FC1'])
def test_sensor_qos_depth_units_and_frame_headers(graph, encoding):
    harness, detector, received, pubs, wait, pump, images = graph
    images(encoding)
    wait(lambda: bool(received['coords']) and bool(received['detections']))
    coords = received['coords'][-1]
    assert coords.header.frame_id == 'world'
    obj = coords.objects[0]
    assert obj.class_name == 'bottle'
    assert (obj.point.x, obj.point.y, obj.point.z) == pytest.approx((2.0, 0.0, 0.0))
    assert received['detections'][0].header.frame_id == 'camera_color_optical_frame'
    count = len(received['detections'])
    pump()
    assert len(received['detections']) == count, 'Repeated processing of the same image'


def test_unsynchronized_images_and_wrong_pose_frame_do_not_publish_coords(graph):
    harness, detector, received, pubs, wait, pump, images = graph
    images(offset=0.1)
    pump()
    assert not received['detections']
    images(odom_frame='unrelated_frame')
    wait(lambda: bool(received['detections']))
    assert not received['coords']


def test_instruction_to_goal_and_obstacle_avoiding_path(graph, tmp_path):
    harness, detector, received, pubs, wait, pump, images = graph
    executable = FilePath(get_package_prefix('vln_planner')) / 'lib/vln_planner/a_star_planner_node'
    with (tmp_path / 'planner.log').open('w') as log:
        process = subprocess.Popen([str(executable), '--ros-args', '-p', 'resolution:=0.1',
                                    '-p', 'grid_width:=80', '-p', 'grid_height:=80'],
                                   stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
        try:
            wait(lambda: pubs['cloud'].get_subscription_count() >= 1
                 and pubs['odom'].get_subscription_count() >= 3
                 and pubs['goal'].get_subscription_count() >= 1)
            pump()
            images()
            wait(lambda: bool(received['coords']))
            # A wall blocks the straight route at x=1; the path must go around it.
            wall = [(1.0, float(y), 1.5) for y in np.arange(-0.5, 0.6, 0.1)]
            cloud = point_cloud2.create_cloud_xyz32(
                Header(stamp=harness.get_clock().now().to_msg(), frame_id='world'), wall)
            pubs['instruction'].publish(String(data='bottle'))
            wait(lambda: bool(received['goals']))
            pump()
            assert not received['paths'], 'Planner must wait for its first point cloud'
            pubs['cloud'].publish(cloud)
            wait(lambda: bool(received['paths']))
            assert process.poll() is None
            assert received['goals'][-1].header.frame_id == 'world'
            path = received['paths'][-1]
            assert path.header.frame_id == 'world'
            assert path.poses[0].pose.position.x == pytest.approx(0.0)
            assert path.poses[-1].pose.position.x == pytest.approx(2.0)
            assert max(abs(p.pose.position.y) for p in path.poses) > 0.6
            # An out-of-grid goal produces an empty path rather than a clamped destination.
            goal = PoseStamped(header=Header(frame_id='world'))
            goal.pose.position.x = 100.0
            goal.pose.orientation.w = 1.0
            received['paths'].clear()
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
