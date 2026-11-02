"""Owned, private Unix-socket broker retaining one approved Xcode MCP connection."""
import argparse
import fcntl
import json
import os
import pathlib
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

from reloop.core import PROJECT_ROOT, atomic, load, now
from reloop.mcp_client import Client

DIRECTORY = PROJECT_ROOT / 'research/state/xcode-bridge'
TOOLS = {'XcodeListWindows', 'XcodeGlob', 'XcodeRead', 'RenderPreview'}
LIMIT = 8 * 1024 * 1024


def identity(pid):
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'command='],
                            capture_output=True, text=True, timeout=5, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def installed_xcode():
    result = subprocess.run(['ps', '-axo', 'pid=,comm='], capture_output=True,
                            text=True, timeout=5, check=True)
    pids = [int(line.strip().split(None, 1)[0]) for line in result.stdout.splitlines()
            if line.strip().endswith('/Applications/Xcode.app/Contents/MacOS/Xcode')]
    if len(pids) != 1:
        raise RuntimeError('Require exactly one installed Xcode process')
    return pids[0]


def validate_request(request):
    method = request.get('method')
    if method not in {'status', 'tools/list', 'tools/call'}:
        raise ValueError('Broker method not allowed')
    params = request.get('params', {})
    if not isinstance(params, dict):
        raise ValueError('Parameters must be an object')
    if method == 'tools/call' and params.get('name') not in TOOLS:
        raise ValueError('Broker tool not allowed')
    return method, params


def serve(directory=DIRECTORY, command=None):
    directory = pathlib.Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    lock_fd = os.open(str(directory / 'broker.lock'), os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    endpoint = directory / 'broker.sock'
    endpoint.unlink(missing_ok=True)
    env = dict(os.environ)
    xcode_pid = installed_xcode() if command is None else None
    session = str(uuid.uuid4())
    if xcode_pid is not None:
        env.update(MCP_XCODE_PID=str(xcode_pid), MCP_XCODE_SESSION_ID=session)
    client = None
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    record = {'pid': os.getpid(), 'identity': identity(os.getpid()), 'started_at': now(),
              'session_id': session, 'xcode_pid': xcode_pid, 'initialized': False,
              'scope': 'One retained approved connection; no auto-restart or permission bypass'}
    def shutdown(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, shutdown)
    try:
        with (directory / 'bridge.stderr').open('ab') as stderr:
            client = Client(command or ['xcrun', 'mcpbridge'], stderr, timeout=90, env=env)
            record.update(initialized=True, bridge_pid=client.process.pid)
            atomic(directory / 'record.json', record)
            server.bind(str(endpoint));os.chmod(endpoint, 0o600)
            server.listen(4);server.settimeout(1)
            while True:
                try:
                    connection, _ = server.accept()
                except socket.timeout:
                    continue
                with connection:
                    connection.settimeout(5)
                    try:
                        with connection.makefile('rb') as stream:
                            data = stream.readline(LIMIT + 1)
                        if len(data) > LIMIT or not data.endswith(b'\n'):
                            raise ValueError('Invalid broker request size/framing')
                        method, params = validate_request(json.loads(data))
                        if method == 'status':
                            response = {'result': record}
                        else:
                            # A timeout is fail-closed: a late result is not assigned to another call.
                            result = client.request(method, params)
                            response = {'result': result, 'broker': record}
                    except Exception as error:
                        response = {'error': str(error), 'error_type': type(error).__name__}
                        if isinstance(error, (TimeoutError, EOFError)):
                            record['unhealthy'] = True
                            atomic(directory / 'record.json', record)
                    try:
                        connection.sendall(json.dumps(response).encode() + b'\n')
                    except (BrokenPipeError, socket.timeout):
                        pass
                    if record.get('unhealthy'):
                        return
    finally:
        server.close()
        if client:
            client.close()
        endpoint.unlink(missing_ok=True)
        os.close(lock_fd)


class BrokerClient:
    """Each caller closes its socket; the approved upstream parent stays alive."""
    def __init__(self, directory=DIRECTORY, timeout=100):
        self.directory = pathlib.Path(directory);self.timeout = timeout
        self.metadata = self.request('status', {})
        self.initialized = self.metadata

    def request(self, method, params):
        request = {'method': method, 'params': params}
        validate_request(request)
        endpoint = self.directory / 'broker.sock'
        for path, kind in [(self.directory, stat.S_ISDIR), (endpoint, stat.S_ISSOCK)]:
            info = path.lstat()
            if not kind(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise RuntimeError('Broker endpoint must be private and owned by this user')
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(self.timeout);connection.connect(str(endpoint))
            connection.sendall(json.dumps(request).encode() + b'\n')
            with connection.makefile('rb') as stream:
                data = stream.readline(32 * LIMIT + 1)
            if len(data) > 32 * LIMIT or not data.endswith(b'\n'):
                raise RuntimeError('Invalid broker response size/framing')
        response = json.loads(data)
        if 'error' in response:
            raise RuntimeError(response['error'])
        return response['result']

    def close(self):
        pass


def manage(action, directory=DIRECTORY):
    directory = pathlib.Path(directory)
    prior = load(directory / 'record.json', {})
    alive = bool(prior and identity(prior['pid']) == prior['identity'])
    if action == 'status':
        return {'running': alive, 'record': prior,
                'responsive': bool(alive and (directory / 'broker.sock').exists())}
    if action == 'stop':
        if alive:
            os.kill(prior['pid'], signal.SIGTERM)
        return {'stopped_owned_broker': alive, 'user_xcode_untouched': True}
    if alive:
        return {'already_running': True, 'record': prior}
    directory.mkdir(parents=True, exist_ok=True);os.chmod(directory, 0o700)
    env = dict(os.environ);env['PYTHONPATH'] = str(pathlib.Path(__file__).resolve().parents[1])
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    with (directory / 'broker.log').open('ab') as log:
        process = subprocess.Popen([sys.executable, '-m', 'reloop.xcodebridge'], env=env,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        current = load(directory / 'record.json', {})
        if current.get('pid') == process.pid and (directory / 'broker.sock').exists():
            return {'started': True, 'record': current}
        if process.poll() is not None:
            raise RuntimeError('Owned broker failed startup; inspect local broker.log')
        time.sleep(.1)
    return {'starting': True, 'pid': process.pid}


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.parse_args()
    try:
        serve()
    except KeyboardInterrupt:
        pass
