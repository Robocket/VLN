"""Play a ROS 2 bag and show its images in OpenCV desktop windows."""

import argparse
import math
import os
from pathlib import Path
import signal
import subprocess

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rosbag2_interfaces.srv import TogglePaused
import rosbag2_py
from sensor_msgs.msg import Image


def depth_preview(depth, encoding, max_depth=5.0):
    if not math.isfinite(max_depth) or max_depth <= 0:
        raise ValueError('depth-max must be finite and positive')
    if encoding not in ('16UC1', 'mono16', '32FC1'):
        raise ValueError(f'Unsupported depth encoding: {encoding}')
    meters = depth.astype(np.float32) * (0.001 if encoding != '32FC1' else 1.0)
    valid = np.isfinite(meters) & (meters > 0)
    normalized = np.zeros(meters.shape, dtype=np.uint8)
    normalized[valid] = np.clip(meters[valid] / max_depth * 255, 0, 255).astype(np.uint8)
    image = cv2.applyColorMap(normalized, cv2.COLORMAP_TURBO)
    image[~valid] = 0
    return image


def validate_bag(path, image_topic, depth_topic=None):
    if not path.exists():
        raise ValueError(f'Bag does not exist: {path}')
    if path.is_file() and path.suffix not in ('.mcap', '.db3'):
        raise ValueError('Use the converted ROS 2 bag directory, not the original ROS 1 .bag')
    reader = rosbag2_py.SequentialReader()
    storage = '' if path.is_dir() else ('mcap' if path.suffix == '.mcap' else 'sqlite3')
    reader.open(rosbag2_py.StorageOptions(uri=str(path), storage_id=storage),
                rosbag2_py.ConverterOptions('', ''))
    topics = {item.name: item.type for item in reader.get_all_topics_and_types()}
    for topic in filter(None, (image_topic, depth_topic)):
        if topics.get(topic) != 'sensor_msgs/msg/Image':
            raise ValueError(f'Image topic is missing or has a different type: {topic}')


def player_command(args):
    command = ['ros2', 'bag', 'play', str(args.bag), '--clock', '--disable-keyboard-controls',
               '--delay', str(args.delay), '--rate', str(args.rate), '--start-offset', str(args.start_offset)]
    if args.loop:
        command.append('--loop')
    if args.duration is not None:
        command += ['--playback-duration', str(args.duration)]
    if args.exclude_topics:
        command += ['--exclude-topics', *args.exclude_topics]
    return command


class ImageViewer(Node):
    def __init__(self, args):
        super().__init__('vln_bag_image_viewer')
        self.bridge = CvBridge()
        self.args = args
        self.images = {}
        self.counts = {'color': 0, 'depth': 0}
        self.windows = {'color': 'Bag: Color | Space pause/resume | Q/Esc quit'}
        if args.show_depth:
            self.windows['depth'] = 'Bag: Depth | Space pause/resume | Q/Esc quit'
        self.create_subscription(Image, args.image_topic, lambda msg: self.receive('color', msg),
                                 qos_profile_sensor_data)
        if args.show_depth:
            self.create_subscription(Image, args.depth_topic, lambda msg: self.receive('depth', msg),
                                     qos_profile_sensor_data)
        self.pause_client = self.create_client(TogglePaused, '/rosbag2_player/toggle_paused')
        self.pause_future = None

    def receive(self, name, msg):
        try:
            if name == 'depth':
                image = depth_preview(self.bridge.imgmsg_to_cv2(msg, 'passthrough'),
                                      msg.encoding, self.args.depth_max)
            else:
                image = self.bridge.imgmsg_to_cv2(msg, 'bgr8').copy()
            stamp = msg.header.stamp
            text = f'{name}  t={stamp.sec}.{stamp.nanosec:09d}'
            if name == 'depth':
                text += f'  range: 0..{self.args.depth_max:g} m'
            cv2.rectangle(image, (0, 0), (image.shape[1]-1, 25), (20, 20, 20), -1)
            cv2.putText(image, text, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            self.images[name] = image
            self.counts[name] += 1
        except Exception as exc:
            self.get_logger().warning(f'Image conversion failed: {exc}', throttle_duration_sec=5.0)

    def open_windows(self):
        for index, (name, title) in enumerate(self.windows.items()):
            cv2.namedWindow(title, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(title, 640, 480)
            cv2.moveWindow(title, 40+index*660, 80)
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(image, f'Waiting for {name} images...', (35, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (220, 220, 220), 1)
            cv2.imshow(title, image)
        cv2.waitKey(1)

    def draw(self):
        for name, title in self.windows.items():
            try:
                visible = cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE)
            except cv2.error:
                return False
            if visible < 1:
                return False
            if name in self.images:
                cv2.imshow(title, self.images[name])
        key = cv2.waitKey(15) & 0xff
        if key in (27, ord('q'), ord('Q')):
            return False
        if key == ord(' ') and (self.pause_future is None or self.pause_future.done()):
            if self.pause_client.service_is_ready():
                self.pause_future = self.pause_client.call_async(TogglePaused.Request())
            else:
                self.get_logger().info('Bag player is not ready to pause yet')
        return True


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bag', type=Path, default=Path('data/bags/vln_0420_ros2'))
    parser.add_argument('--image-topic', default='/camera/color/image_raw')
    parser.add_argument('--show-depth', action='store_true', help='Also open a colorized depth window')
    parser.add_argument('--depth-topic', default='/camera/depth/image_rect_raw')
    parser.add_argument('--depth-max', type=float, default=5.0, help='Depth display range in meters')
    parser.add_argument('--rate', type=float, default=1.0)
    parser.add_argument('--loop', action='store_true')
    parser.add_argument('--start-offset', type=float, default=0.0)
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--duration', type=float, help='Stop after this many seconds of bag time')
    parser.add_argument('--keep-open', action='store_true', help='Keep the last image after playback ends')
    parser.add_argument('--exclude-topics', nargs='+', default=[], help='Topics not to replay')
    args = parser.parse_args(argv)
    for name in ('rate', 'depth_max'):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) <= 0:
            parser.error(f'--{name.replace("_", "-")} must be finite and positive')
    for name in ('delay', 'start_offset'):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) < 0:
            parser.error(f'--{name.replace("_", "-")} must be finite and nonnegative')
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0):
        parser.error('--duration must be finite and positive')
    if args.image_topic in args.exclude_topics or (args.show_depth and args.depth_topic in args.exclude_topics):
        parser.error('A displayed image topic cannot also be excluded')
    args.bag = args.bag.expanduser().resolve()
    return args


def main(argv=None):
    args = arguments(argv)
    validate_bag(args.bag, args.image_topic, args.depth_topic if args.show_depth else None)
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
            or os.environ.get('QT_QPA_PLATFORM') in ('offscreen', 'minimal')):
        raise SystemExit('Image windows need a graphical desktop; run this script in a desktop terminal')
    rclpy.init()
    node = process = None
    exit_code = 0
    try:
        node = ImageViewer(args)
        # Open GUI before starting playback, so a display error cannot orphan a player.
        node.open_windows()
        print('Space: pause/resume | Q/Esc or close a window: quit', flush=True)
        process = subprocess.Popen(player_command(args))
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.005)
            if not node.draw():
                break
            if process.poll() is not None:
                exit_code = process.returncode
                if exit_code or not args.keep_open:
                    break
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        cv2.destroyAllWindows()
        if node is not None:
            print(f'Displayed image messages: color={node.counts["color"]}, depth={node.counts["depth"]}', flush=True)
            if process is not None and process.returncode == 0 and node.counts['color'] == 0:
                node.get_logger().warning('Playback ended without receiving a color image')
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
