"""Select an observed object from a topic instruction and publish a goal."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import math
from pathlib import Path
import re
import signal

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from vln_interfaces.msg import ObjectCoordinates


def select_index(instruction, objects, robot_position, llm=None):
    """Use exact class names directly; constrain LLM output to a valid index."""
    exact = [i for i, obj in enumerate(objects)
             if obj.class_name.casefold() == instruction.strip().casefold()]
    if exact:
        return exact[0]
    if llm is None:
        raise ValueError('Use an observed class name, or configure llm_model_path for natural language')
    origin = robot_position or (0.0, 0.0, 0.0)
    descriptions = []
    for i, obj in enumerate(objects):
        point = (obj.point.x, obj.point.y, obj.point.z)
        distance = math.dist(point, origin)
        descriptions.append(f'[{i}] {obj.class_name}: {point}, distance={distance:.2f}m')
    prompt = (
        '<|im_start|>system\n你是目标选择器。只输出一个物体索引数字，禁止解释和思考。\n'
        f'机器人坐标：{origin}\n物体列表：\n' + '\n'.join(descriptions)
        + '<|im_end|>\n<|im_start|>user\n' + instruction + ' /no_think'
        + '<|im_end|>\n<|im_start|>assistant\n')
    result = llm.create_completion(prompt=prompt, max_tokens=64, temperature=0.0,
                                   stop=['<|im_end|>'], stream=False)
    output = result['choices'][0]['text'].strip()
    # Some Qwen templates emit an empty reasoning block even with /no_think.
    output = re.sub(r'^<think>\s*</think>\s*', '', output).strip()
    if not re.fullmatch(r'\d+', output):
        raise ValueError(f'LLM must return one integer index, received {output!r}')
    index = int(output)
    if index >= len(objects):
        raise ValueError(f'LLM index {index} is outside the observed object list')
    return index


class GoalSelector(Node):
    def __init__(self, **kwargs):
        super().__init__('llm_goal_selector', **kwargs)
        self.declare_parameters('', [
            ('llm_model_path', ''), ('llm_context_size', 4096),
            ('llm_threads', 16), ('llm_gpu_layers', -1),
            ('frame_id', 'world'), ('goal_height', 0.0), ('max_object_age', 30.0),
            ('odom_topic', '/Odometry'), ('instruction_topic', '/vln/instruction'),
        ])
        self.objects = None
        self.robot_position = None
        self.llm = None
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.goal_pub = self.create_publisher(PoseStamped, '/vln_goal', 10)
        self.create_subscription(ObjectCoordinates, '/object/absolute_coords_list', self.on_objects, 1)
        self.create_subscription(Odometry, self.param('odom_topic'), self.on_odom, qos_profile_sensor_data)
        self.create_subscription(String, self.param('instruction_topic'), self.on_instruction, 10)
        self.create_timer(0.05, self.finish_selection)
        self.get_logger().info('Waiting for /vln/instruction; exact class names work without an LLM')

    def param(self, name):
        return self.get_parameter(name).value

    def on_objects(self, msg):
        if msg.header.frame_id != self.param('frame_id'):
            self.get_logger().warning(f'Ignoring objects in frame {msg.header.frame_id!r}')
            return
        self.objects = msg

    def on_odom(self, msg):
        if msg.header.frame_id == self.param('frame_id'):
            p = msg.pose.pose.position
            self.robot_position = (p.x, p.y, p.z)

    def objects_fresh(self, msg):
        age = (self.get_clock().now().nanoseconds * 1e-9
               - msg.header.stamp.sec - msg.header.stamp.nanosec * 1e-9)
        return 0.0 <= age <= self.param('max_object_age')

    def on_instruction(self, msg):
        if not msg.data.strip():
            return
        if self.pending is not None:
            self.get_logger().warning('Selection in progress; retry after the current instruction finishes')
            return
        if self.objects is None or not self.objects.objects or not self.objects_fresh(self.objects):
            self.get_logger().warning('No recent object coordinates available')
            return
        snapshot = deepcopy(self.objects)
        self.pending = self.pool.submit(self.select_goal, msg.data, snapshot, self.robot_position)

    def select_goal(self, instruction, snapshot, robot_position):
        # Loading and inference run outside the ROS executor so subscriptions remain responsive.
        exact = any(obj.class_name.casefold() == instruction.strip().casefold()
                    for obj in snapshot.objects)
        model_path = self.param('llm_model_path')
        if not exact and self.llm is None and model_path:
            model = Path(model_path).expanduser()
            if not model.is_file():
                raise ValueError(f'LLM model not found: {model}')
            from llama_cpp import Llama
            self.llm = Llama(model_path=str(model), n_ctx=self.param('llm_context_size'),
                             n_threads=self.param('llm_threads'),
                             n_gpu_layers=self.param('llm_gpu_layers'), verbose=False)
        index = select_index(instruction, snapshot.objects, robot_position, self.llm)
        return snapshot, snapshot.objects[index]

    def finish_selection(self):
        if self.pending is None or not self.pending.done():
            return
        pending, self.pending = self.pending, None
        try:
            snapshot, selected = pending.result()
            if not self.objects_fresh(snapshot):
                raise ValueError('Object coordinates expired during selection; send the instruction again')
            goal = PoseStamped(header=deepcopy(snapshot.header))
            goal.header.stamp = self.get_clock().now().to_msg()
            goal.pose.position = deepcopy(selected.point)
            goal.pose.position.z = self.param('goal_height')
            goal.pose.orientation.w = 1.0
            self.goal_pub.publish(goal)
            self.get_logger().info(f'Published goal for {selected.class_name}')
        except Exception as exc:
            self.get_logger().error(f'Goal selection failed: {exc}')

    def destroy_node(self):
        self.pool.shutdown(wait=True, cancel_futures=True)
        if self.llm is not None:
            self.llm.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = GoalSelector()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
