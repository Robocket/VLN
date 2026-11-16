import json
from pathlib import Path
import socketserver
import sys
import threading

from vln_perception.streamer import SocketClient, StreamerSettings


def test_reference_settings_and_existing_parent_assets(tmp_path):
    root = tmp_path / 'robot-agent'
    integration = root / 'modules/OneStreamer/robot_integration'
    integration.mkdir(parents=True)
    (integration / 'live_config.json').write_text(json.dumps({
        'camera': {'enabled': True}, 'ros': {'sample_fps': 4, 'worker_timeout': 600},
        'inference': {'max_frames': 16, 'max_new_tokens': 128, 'max_image_pixels': 50176,
                      'temperature': 0.7, 'visual_cache': True, 'profile': False,
                      'model_path': 'models/onestreamer/OneStreamer-4B'}}))
    (integration / 'live_worker.py').touch()
    (root / 'configs').mkdir()
    (root / 'configs/onestreamer-fast.json').write_text(json.dumps({
        'ros': {'sample_fps': 8}, 'inference': {'max_frames': 4, 'max_new_tokens': 8, 'temperature': 0.0}}))
    model = tmp_path / 'models/onestreamer/OneStreamer-4B'
    model.mkdir(parents=True)
    settings = StreamerSettings.load(root, python=sys.executable)
    assert settings.sample_fps == 8
    assert settings.model == model
    assert settings.inference['max_frames'] == 4
    assert settings.inference['max_new_tokens'] == 8
    assert settings.grounding_tokens == 256
    assert settings.inference['visual_cache']
    command = settings.command('/tmp/test-worker.sock')
    assert command[:2] == [sys.executable, '-u']
    assert Path(command[2]).name == 'gpu_worker.py'
    assert command[command.index('--integration-dir')+1] == str(integration)
    assert command[command.index('--socket')+1] == '/tmp/test-worker.sock'


def test_socket_client_preserves_one_streaming_connection(tmp_path):
    connections, requests = [], []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            connections.append(1)
            while line := self.rfile.readline():
                request = json.loads(line)
                requests.append(request)
                self.wfile.write(json.dumps({'ok': True, 'round': len(requests)}).encode()+b'\n')
                self.wfile.flush()

    path = str(tmp_path / 'worker.sock')
    server = socketserver.UnixStreamServer(path, Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = SocketClient(path, timeout=1, startup_timeout=1)
    try:
        assert client.infer({'frames': [1]})['round'] == 1
        assert client.infer({'frames': [2]})['round'] == 2
        assert len(connections) == 1
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
