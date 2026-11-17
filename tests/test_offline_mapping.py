import json
from types import SimpleNamespace

import numpy as np
import rclpy
from cv_bridge import CvBridge
from nav_msgs.msg import Odometry
from rclpy.parameter import Parameter
from rclpy.serialization import serialize_message
from rclpy.time import Time
import rosbag2_py
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header

from vln_perception.offline_mapping import BagInput, OfflineMapper
from vln_perception.semantic_node import SemanticNode


class ScriptedClient:
    def __init__(self):
        self.requests = []

    def infer(self, request):
        self.requests.append(request)
        response = None if len(self.requests) == 1 else 'A room with desks and chairs.'
        return {'ok': True, 'question': request['question'],
                'source_start_ns': request['frames'][0]['stamp_ns'],
                'source_end_ns': request['frames'][-1]['stamp_ns'],
                'raw': '</Silence>' if response is None else '</Response>'+response,
                'tokens': {'ids': [151670, 41, 42, 151645], 'source': 'model.generate',
                           'triggered': response is not None,
                           'text': '</Silence>' if response is None else '</Response>'+response},
                'response': response}

    def close(self):
        pass


def make_bag(path):
    writer = rosbag2_py.SequentialWriter()
    writer.open(rosbag2_py.StorageOptions(uri=str(path), storage_id='sqlite3'),
                rosbag2_py.ConverterOptions('', ''))
    for index, (topic, msgtype) in enumerate([
            ('/camera/color/image_raw', 'sensor_msgs/msg/Image'),
            ('/cloud_registered', 'sensor_msgs/msg/PointCloud2'),
            ('/Odometry', 'nav_msgs/msg/Odometry')]):
        writer.create_topic(rosbag2_py.TopicMetadata(id=index, name=topic, type=msgtype,
                                                    serialization_format='cdr'))
    for i in range(9):
        timestamp = 1_000_000_000+i*100_000_000
        image = CvBridge().cv2_to_imgmsg(np.zeros((8, 8, 3), np.uint8), 'bgr8')
        image.header = Header(stamp=Time(nanoseconds=timestamp).to_msg(), frame_id='camera_optical_frame')
        # Future cloud/pose timestamps exercise offline nearest matching rather than arrival order.
        odom = Odometry(header=Header(stamp=Time(nanoseconds=timestamp+5_000_000).to_msg(), frame_id='world'))
        odom.pose.pose.orientation.w = 1.0
        cloud = point_cloud2.create_cloud_xyz32(
            Header(stamp=Time(nanoseconds=timestamp+10_000_000).to_msg(), frame_id='world'),
            [(2.0, -0.1, -0.1), (2.0, 0.1, -0.1), (2.0, 0.0, 0.1)])
        for topic, message, stamp in [('/camera/color/image_raw', image, timestamp),
                                      ('/Odometry', odom, timestamp+5_000_000),
                                      ('/cloud_registered', cloud, timestamp+10_000_000)]:
            writer.write(topic, serialize_message(message), stamp)
    writer.close()


def test_complete_bag_waits_for_each_window_flushes_tail_and_only_fuses_real_responses(tmp_path):
    bag_path = tmp_path/'input'
    make_bag(bag_path)
    output = tmp_path/'map'
    output.mkdir()
    client = ScriptedClient()
    rclpy.init()
    node = None
    try:
        node = SemanticNode(settings=SimpleNamespace(sample_fps=20.0, timeout=1.0), client=client,
                            parameter_overrides=[
                                Parameter('start_worker', value=False),
                                Parameter('fx', value=4.0), Parameter('fy', value=4.0),
                                Parameter('cx', value=4.0), Parameter('cy', value=4.0),
                                Parameter('image_width', value=8), Parameter('image_height', value=8)])
        mapper = OfflineMapper(node, BagInput(bag_path), output, 0.05)
        mapper.run()
        assert mapper.counts['images'] == mapper.counts['sampled_images'] == 9
        assert mapper.counts['windows'] == 3
        assert mapper.counts['silence'] == 1
        assert mapper.counts['annotated_events'] == 2
        assert [len(x['frames']) for x in client.requests] == [4, 4, 1]
        assert {x['version'] for x in client.requests} == {0}, 'Do not force periodic session resets'
        assert len(mapper.map.voxels) == 3
        records = mapper.map.records({1: 'A room with desks and chairs.'})
        assert set(records['label_id']) == {1}
        assert set(records['observations']) == {2}
        offsets, event_ids = mapper.map.event_links()
        assert event_ids.tolist() == [1, 2]*3
        assert offsets.tolist() == [0, 2, 4, 6]
        assert mapper.scene_events[1]['token_ids'] == [151670, 41, 42, 151645]
        assert mapper.scene_events[2]['description'] == 'A room with desks and chairs.'
        assert len(list((output/'events').glob('*.npz'))) == 2
        states = [json.loads(line) for line in (output/'states.jsonl').read_text().splitlines()]
        assert states[-1]['source_cloud_ns'] == 1_810_000_000
        assert states[-1]['source_end_ns'] == 1_800_000_000
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
