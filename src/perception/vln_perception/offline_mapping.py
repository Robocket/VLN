"""Index a ROS 2 bag, infer its sampled image stream, and export a semantic map."""

import argparse
import base64
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path
import tempfile
import time

import cv2
import numpy as np
import rclpy
from rclpy.parameter import Parameter
from rclpy.serialization import deserialize_message
import rosbag2_py
from rosidl_runtime_py.utilities import get_message
import yaml

from .mapping import VoxelSemanticMap, export_map
from .projection import parse_scene_response, scene_records
from .semantic_node import SemanticNode, stamp_ns
from .streamer import DEFAULT_ROOT, SocketClient, StreamerSettings, WorkerProcess


class BagInput:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        if self.path.is_dir():
            metadata = yaml.safe_load((self.path / 'metadata.yaml').read_text())['rosbag2_bagfile_information']
            self.storage = metadata['storage_identifier']
        elif self.path.suffix in ('.mcap', '.db3'):
            self.storage = 'mcap' if self.path.suffix == '.mcap' else 'sqlite3'
        else:
            raise ValueError('Pass a ROS 2 bag directory or MCAP/DB3 file; the original ROS 1 .bag needs conversion')

    def messages(self, topics):
        reader = rosbag2_py.SequentialReader()
        reader.open(rosbag2_py.StorageOptions(uri=str(self.path), storage_id=self.storage),
                    rosbag2_py.ConverterOptions('', ''))
        available = {item.name: item.type for item in reader.get_all_topics_and_types()}
        wanted = [topic for topic in topics if topic in available]
        if not wanted:
            return
        types = {topic: get_message(available[topic]) for topic in wanted}
        reader.set_filter(rosbag2_py.StorageFilter(topics=wanted))
        while reader.has_next():
            topic, raw, recorded_ns = reader.read_next()
            yield topic, deserialize_message(raw, types[topic]), recorded_ns


class TimeIndex:
    def __init__(self, messages):
        self.items = sorted(messages, key=lambda msg: stamp_ns(msg.header.stamp))
        self.stamps = [stamp_ns(msg.header.stamp) for msg in self.items]

    def nearest(self, timestamp):
        if not self.items:
            return None
        index = bisect_left(self.stamps, timestamp)
        choices = [x for x in (index-1, index) if 0 <= x < len(self.items)]
        return self.items[min(choices, key=lambda x: (abs(self.stamps[x]-timestamp), x))]

    def calibration(self, timestamp):
        if not self.items:
            return None
        return self.items[max(0, bisect_right(self.stamps, timestamp)-1)]


def read_parameters(path):
    data = yaml.safe_load(Path(path).expanduser().read_text()) or {}
    result = dict(data.get('/**', {}).get('ros__parameters', {}))
    result.update(data.get('streaming_semantic_node', {}).get('ros__parameters', {}))
    return result


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bag', default='data/vln_0420_ros2')
    parser.add_argument('--output', help='New output directory; existing directories are never overwritten')
    parser.add_argument('--params-file', default='src/bringup/config/vln.yaml')
    parser.add_argument('--voxel-size', type=float, default=0.05, help='Voxel edge length in meters')
    parser.add_argument('--task', help='Override the continuous proactive task, without resetting it per window')
    parser.add_argument('--socket-path', help='Use a dedicated socket path')
    parser.add_argument('--reuse-worker', action='store_true', help='Connect an existing VLN semantic worker')
    parser.add_argument('--description-tokens', type=int, help='Maximum tokens in a proactive scene description')
    parser.add_argument('--ros-domain-id', type=int, default=94, help='Isolated local ROS context for projection helpers')
    parser.add_argument('--window-timeout', type=float, default=600.0)
    parser.add_argument('--no-event-files', action='store_true', help='Skip individual event NPZ and image files')
    return parser.parse_args(argv)


class OfflineMapper:
    def __init__(self, node, bag, output, voxel_size, save_events=True):
        self.node, self.bag, self.output = node, bag, Path(output)
        self.map = VoxelSemanticMap(voxel_size, node.param('frame_id'))
        self.save_events = save_events
        self.counts = Counter()
        self.skip_reasons = Counter()
        self.states = []
        self.scene_events = {}
        self.generation = 0

    def index_inputs(self):
        node = self.node
        clouds, odoms, infos = [], [], []
        self.transforms = []
        topics = {node.param('cloud_topic'), node.param('odom_topic'), node.param('camera_info_topic')}
        if node.tf_buffer is not None:
            topics.update(('/tf', '/tf_static'))
        for topic, msg, _ in self.bag.messages(topics):
            if topic == node.param('cloud_topic'):
                clouds.append(msg)
            elif topic == node.param('odom_topic'):
                odoms.append(msg)
            elif topic == node.param('camera_info_topic'):
                infos.append(msg)
            elif topic == '/tf_static':
                for transform in msg.transforms:
                    node.tf_buffer.set_transform_static(transform, 'offline_bag')
            elif topic == '/tf':
                self.transforms.extend(msg.transforms)
        if not clouds or (node.tf_buffer is None and not odoms):
            raise ValueError('Bag is missing the configured registered cloud or odometry topic')
        self.clouds, self.odoms, self.infos = TimeIndex(clouds), TimeIndex(odoms), TimeIndex(infos)
        self.counts.update(indexed_clouds=len(clouds), indexed_odometry=len(odoms), indexed_camera_info=len(infos))
        self.transforms.sort(key=lambda msg: stamp_ns(msg.header.stamp))
        self.transform_index = 0
        print(f'Indexed {len(clouds)} clouds, {len(odoms)} odometry messages, '
              f'{len(infos)} CameraInfo messages', flush=True)

    def snapshot(self, image):
        node = self.node
        timestamp = stamp_ns(image.header.stamp)
        node.clouds.clear()
        node.clouds.append(self.clouds.nearest(timestamp))
        node.odoms.clear()
        if self.odoms.items:
            node.odoms.append(self.odoms.nearest(timestamp))
        node.camera_info = self.infos.calibration(timestamp)
        # Load a small future bracket for interpolation, not a latest-time transform.
        while (self.transform_index < len(self.transforms)
               and stamp_ns(self.transforms[self.transform_index].header.stamp)
               <= timestamp + node.param('sync_tolerance')*1e9):
            node.tf_buffer.set_transform(self.transforms[self.transform_index], 'offline_bag')
            self.transform_index += 1
        return node.snapshot(image)

    def process_window(self, batch, log):
        node = self.node
        request = {'question': node.task,
                   'version': self.generation, 'sample_fps': node.settings.sample_fps,
                   'frames': [{'stamp_ns': stamp_ns(snapshot.header.stamp), 'jpeg': jpeg}
                              for snapshot, jpeg in batch]}
        started = time.monotonic()
        result = node.client.infer(request)
        if (result.get('source_start_ns') != request['frames'][0]['stamp_ns']
                or result.get('source_end_ns') != request['frames'][-1]['stamp_ns']
                or result.get('question') != request['question']):
            raise ValueError('Worker returned a result for the wrong image window')
        self.counts['windows'] += 1
        state = {key: value for key, value in result.items() if key != 'keyframes'}
        state.update(window=self.counts['windows'], source_cloud_ns=batch[-1][0].cloud_stamp_ns,
                     elapsed_s=round(time.monotonic()-started, 3))
        state['frame_count'] = len(batch)
        if result.get('response') is None:
            self.counts['standby' if '</Standby>' in result.get('raw', '') else 'silence'] += 1
        else:
            self.counts['responses'] += 1
            try:
                description = parse_scene_response(result)
                snapshot = batch[-1][0]
                event_id = self.counts['annotated_events'] + 1
                records, event = scene_records(snapshot, description, node.label_ids, event_id)
                event.update(window=state['window'], stamp_ns=stamp_ns(snapshot.header.stamp),
                             source_cloud_ns=snapshot.cloud_stamp_ns, source_pose_ns=snapshot.pose_stamp_ns,
                             frame_id=snapshot.frame_id, image_frame_id=snapshot.header.frame_id)
                state['scene_event'] = event
                state['visible_points'] = state['labeled_points'] = len(records)
                if len(records):
                    self.map.add(records, snapshot.frame_id)
                    self.scene_events[event_id] = event
                    self.counts['annotated_events'] += 1
                    if self.save_events:
                        self.save_event(snapshot, records, event)
            except (ValueError, TypeError) as exc:
                self.counts['rejected_descriptions'] += 1
                state['annotation_error'] = str(exc)
        log.write(json.dumps(state, ensure_ascii=False)+'\n')
        log.flush()
        self.states.append({key: state[key] for key in
                            ('window', 'source_end_ns', 'elapsed_s', 'labeled_points', 'annotation_error') if key in state})
        print(f'Window {self.counts["windows"]:03d} '
              f'{"Response" if result.get("response") is not None else result.get("raw", "Silence")} '
              f'points={state.get("labeled_points", 0)} '
              f'map_voxels={len(self.map.voxels)} time={state["elapsed_s"]:.2f}s', flush=True)

    def save_event(self, snapshot, records, event):
        directory = self.output / 'events'
        directory.mkdir(exist_ok=True)
        prefix = directory / f'{event["event_id"]:04d}_{stamp_ns(snapshot.header.stamp)}'
        np.savez_compressed(str(prefix)+'.npz', points=records, frame_id=snapshot.frame_id)
        Path(str(prefix)+'.json').write_text(json.dumps(event, indent=2, ensure_ascii=False)+'\n')
        image = snapshot.image.copy()
        for (u, v), color in zip(snapshot.uv, records['rgb']):
            color = int(color)
            image[v, u] = [color & 255, (color >> 8) & 255, (color >> 16) & 255]
        cv2.putText(image, f'Scene {event["event_id"]} | label_id={event["label_id"]}', (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if not cv2.imwrite(str(prefix)+'.png', image):
            raise OSError('Could not save event projection')

    def run(self):
        self.index_inputs()
        node = self.node
        batch = []
        last_sampled = previous = None
        with (self.output / 'states.jsonl').open('w') as log:
            for _, image, _ in self.bag.messages({node.param('color_topic')}):
                self.counts['images'] += 1
                timestamp = stamp_ns(image.header.stamp)
                if previous is not None and timestamp < previous:
                    self.generation += 1
                    batch.clear()
                    last_sampled = None
                    self.counts['clock_resets'] += 1
                previous = timestamp
                if last_sampled is not None and timestamp-last_sampled < 1e9/node.settings.sample_fps:
                    continue
                try:
                    snapshot = self.snapshot(image)
                except Exception as exc:
                    self.counts['skipped_images'] += 1
                    self.skip_reasons[str(exc)] += 1
                    continue
                ok, jpeg = cv2.imencode('.jpg', snapshot.image, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not ok:
                    raise ValueError('Could not encode sampled frame')
                batch.append((snapshot, base64.b64encode(jpeg).decode('ascii')))
                last_sampled = timestamp
                self.counts['sampled_images'] += 1
                if len(batch) == 4:
                    self.process_window(batch, log)
                    batch = []
            if batch:
                self.process_window(batch, log)
        if not self.counts['images']:
            raise ValueError('Bag contains no images on the configured color topic')
        if not self.counts['windows']:
            raise ValueError('No synchronized camera-visible windows could be assembled')


def main(argv=None):
    args = arguments(argv)
    if not np.isfinite(args.window_timeout) or args.window_timeout <= 0:
        raise ValueError('window-timeout must be finite and positive')
    parameters = read_parameters(args.params_file)
    if args.task:
        parameters['task'] = args.task
    if args.description_tokens is not None:
        parameters['description_max_new_tokens'] = args.description_tokens
    parameters['start_worker'] = False
    bag = BagInput(args.bag)
    settings = StreamerSettings.load(parameters.get('robot_agent_root', DEFAULT_ROOT),
        parameters.get('onestreamer_config', 'configs/onestreamer-fast.json'),
        parameters.get('worker_python', ''), parameters.get('model_path', ''),
        parameters.get('description_max_new_tokens', 128))
    VoxelSemanticMap(args.voxel_size, parameters.get('frame_id', 'world'))
    output = Path(args.output or f'data/maps/{bag.path.stem}_scene').expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    node = worker = mapper = None
    started = time.monotonic()
    report = {'bag': str(bag.path), 'output': str(output), 'completed': False,
              'voxel_size_m': args.voxel_size, 'method': 'proactive_scene_description',
              'fusion': 'retain_all_scene_event_links_per_voxel; primary_label_for_color_only',
              'config': parameters, 'streamer': {'sample_fps': settings.sample_fps,
                  'inference': settings.inference,
                  'model': str(settings.model), 'python': str(settings.python)}}
    (output / 'configuration.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    rclpy.init(domain_id=args.ros_domain_id)
    try:
        with tempfile.TemporaryDirectory(prefix='vln-map-') as temporary:
            if args.reuse_worker and not args.socket_path:
                raise ValueError('--reuse-worker requires --socket-path')
            socket_path = args.socket_path or str(Path(temporary) / 'worker.sock')
            client = SocketClient(socket_path, args.window_timeout, parameters.get('startup_timeout', 120.0))
            try:
                node = SemanticNode(settings=settings, client=client,
                                    parameter_overrides=[Parameter(key, value=value) for key, value in parameters.items()])
                mapper = OfflineMapper(node, bag, output, args.voxel_size, not args.no_event_files)
                if not args.reuse_worker:
                    worker = WorkerProcess(settings, socket_path)
                    ready_by = time.monotonic() + parameters.get('startup_timeout', 120.0)
                    while not Path(socket_path).is_socket():
                        if worker.process.poll() is not None:
                            raise RuntimeError(f'OneStreamer worker exited with code {worker.process.returncode}')
                        if time.monotonic() >= ready_by:
                            raise TimeoutError('OneStreamer startup timed out')
                        time.sleep(0.1)
                mapper.run()
                report['completed'] = True
            finally:
                if node is not None:
                    node.destroy_node()
                    node = None
                else:
                    client.close()
                if worker is not None:
                    worker.close()
                    worker = None
    except BaseException as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        if mapper is not None:
            labels = {value: key for key, value in mapper.node.label_ids.items()}
            report.update(export_map(output, mapper.map, labels, mapper.scene_events))
            report.update(counts=dict(mapper.counts), skip_reasons=dict(mapper.skip_reasons),
                          frame_id=mapper.map.frame_id, events=mapper.map.events,
                          input_points=mapper.map.input_points,
                          input_labeled_points=mapper.map.input_labeled_points)
        report['elapsed_s'] = round(time.monotonic()-started, 3)
        report['status'] = ('complete' if report.get('labeled_map_points') else 'no_annotations') if report['completed'] else 'failed'
        (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
        if rclpy.ok():
            rclpy.shutdown()
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    if not report.get('labeled_map_points'):
        raise SystemExit('Bag processed, but no labeled points were produced; inspect states.jsonl and the task')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
