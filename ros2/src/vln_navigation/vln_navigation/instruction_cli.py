"""Interactive terminal companion to the launchable goal selector."""

import select
import signal
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import String


def main(args=None):
    rclpy.init(args=args)
    node = Node('vln_instruction_cli')
    node.declare_parameter('instruction_topic', '/vln/instruction')
    publisher = node.create_publisher(String, node.get_parameter('instruction_topic').value, 10)
    try:
        print('输入目标指令（例如 bottle 或“去最近的椅子”），输入 quit 退出。', flush=True)
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            if not select.select([sys.stdin], [], [], 0.1)[0]:
                continue
            line = sys.stdin.readline()
            if not line or line.strip().lower() in ('q', 'quit', 'exit', 'bye'):
                break
            if line.strip():
                deadline = time.monotonic() + 3.0
                while not publisher.get_subscription_count() and time.monotonic() < deadline and rclpy.ok():
                    rclpy.spin_once(node, timeout_sec=0.1)
                if not publisher.get_subscription_count():
                    node.get_logger().warning('No goal selector subscriber; instruction was not sent')
                    continue
                publisher.publish(String(data=line.strip()))
                rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
