"""Reuse robot-agent's OneStreamer configuration and isolated GPU worker."""

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time


DEFAULT_ROOT = '/home/crl/DDD/EGI/robot-agent'
DEFAULT_SOCKET = str(Path(tempfile.gettempdir()) / f'vln-onestreamer-{os.getuid()}' / 'worker.sock')


@dataclass(frozen=True)
class StreamerSettings:
    root: Path
    worker: Path
    python: Path
    model: Path
    sample_fps: float
    timeout: float
    inference: dict

    @classmethod
    def load(cls, root, config='configs/onestreamer-fast.json', python='', model='', description_tokens=128):
        root = Path(root).expanduser().resolve()
        integration = root / 'modules/OneStreamer/robot_integration'
        base = json.loads((integration / 'live_config.json').read_text())
        config_path = Path(config).expanduser()
        if not config_path.is_absolute():
            config_path = root / config_path
        for group, values in json.loads(config_path.read_text()).items():
            if group not in base or not isinstance(values, dict):
                raise ValueError(f'Invalid OneStreamer config group: {group}')
            for key, value in values.items():
                if key not in base[group]:
                    raise ValueError(f'Unknown OneStreamer config key: {group}.{key}')
                base[group][key] = value
        inf = dict(base['inference'])
        if type(description_tokens) is not int or not 1 <= description_tokens <= 4096:
            raise ValueError('description_tokens must be between 1 and 4096')
        inf['max_new_tokens'] = description_tokens
        fps, timeout = float(base['ros']['sample_fps']), float(base['ros']['worker_timeout'])
        if not math.isfinite(fps) or fps <= 0 or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('OneStreamer sample_fps and worker_timeout must be finite and positive')
        for key, low, high in [('max_frames', 4, 256), ('max_new_tokens', 1, 4096),
                               ('max_image_pixels', 1024, 16777216)]:
            value = inf[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'Invalid inference.{key}')
        if inf['max_frames'] % 4 or not math.isfinite(inf['temperature']) or inf['temperature'] < 0:
            raise ValueError('Invalid OneStreamer window or temperature')
        for key in ('visual_cache', 'profile'):
            if type(inf[key]) is not bool:
                raise ValueError(f'inference.{key} must be boolean')

        def asset(explicit, suffix):
            if explicit:
                path = Path(explicit).expanduser()
                return path if path.is_absolute() else root / path
            for prefix in (root, root.parent):
                path = prefix / suffix
                if path.exists():
                    return path
            return root / suffix

        return cls(root, integration / 'live_worker.py',
                   asset(python, '.envs/onestreamer/bin/python'),
                   asset(model, inf['model_path']), fps, timeout, inf)

    def command(self, socket_path):
        for path in (self.python, self.worker, self.model):
            if not path.exists():
                raise ValueError(f'OneStreamer asset does not exist: {path}')
        inf = self.inference
        adapter = Path(__file__).with_name('gpu_worker.py')
        command = [str(self.python), '-u', str(adapter), '--integration-dir', str(self.worker.parent),
                   '--model', str(self.model),
                   '--socket', socket_path]
        for key in ('max_frames', 'max_new_tokens', 'max_image_pixels', 'temperature'):
            command += ['--' + key.replace('_', '-'), str(inf[key])]
        if not inf['visual_cache']:
            command.append('--no-visual-cache')
        if inf['profile']:
            command.append('--profile')
        return command


class WorkerProcess:
    def __init__(self, settings, socket_path):
        path = Path(socket_path)
        if path.exists() or path.is_symlink():
            raise ValueError(f'Worker socket already exists: {path}; use start_worker:=false to reuse it')
        env = os.environ.copy()
        # ROS runs on Python 3.12; the existing model environment uses Python 3.10.
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['ROBOT_AGENT_ROOT'] = str(settings.root)
        self.process = subprocess.Popen(settings.command(socket_path), cwd=settings.root, env=env)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


class SocketClient:
    """One persistent connection preserves the worker's streaming session."""

    def __init__(self, path, timeout=600.0, startup_timeout=120.0):
        if len(os.fsencode(path)) > 100:
            raise ValueError('Unix socket path is too long')
        self.path, self.timeout, self.startup_timeout = path, timeout, startup_timeout
        self.connection = self.stream = None
        self.closed = False

    def infer(self, request):
        data = (json.dumps(request, ensure_ascii=False) + '\n').encode()
        if len(data) > 12 * 1024 * 1024:
            raise ValueError('OneStreamer input window exceeds the worker protocol limit')
        if self.connection is None:
            deadline = time.monotonic() + self.startup_timeout
            while not self.closed:
                conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                conn.settimeout(self.timeout)
                try:
                    conn.connect(self.path)
                except OSError:
                    conn.close()
                    if time.monotonic() >= deadline:
                        raise TimeoutError('OneStreamer worker did not become ready')
                    time.sleep(0.1)
                    continue
                self.connection = conn
                self.stream = conn.makefile('rwb')
                break
        if self.closed:
            raise ConnectionError('OneStreamer client is closed')
        try:
            self.stream.write(data)
            self.stream.flush()
            line = self.stream.readline(1024 * 1024 + 1)
            if not line or len(line) > 1024 * 1024 or not line.endswith(b'\n'):
                raise ConnectionError('Invalid or oversized OneStreamer response')
            result = json.loads(line)
            if not isinstance(result, dict) or not result.get('ok'):
                raise ValueError(f'OneStreamer failed: {result.get("error") if isinstance(result, dict) else result}')
            return result
        except Exception:
            self._disconnect()
            raise

    def _disconnect(self):
        conn, self.connection = self.connection, None
        stream, self.stream = self.stream, None
        if conn is not None:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if stream is not None:
            stream.close()
        if conn is not None:
            conn.close()

    def close(self):
        self.closed = True
        self._disconnect()
