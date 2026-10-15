#!/usr/bin/env python3
"""Run the original local browser checks; no installation or security overrides."""
import argparse
import functools
import html
import http.server
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time

DEFAULT_CHROME = '/Users/8amps/.local/share/unified-computer-use/chrome/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chrome', default=DEFAULT_CHROME)
    args = parser.parse_args()
    deadline = time.monotonic() + 25
    report = {'status': 'fail', 'browser_version': '', 'version_stderr': '', 'stdout': '', 'stderr': ''}
    server = None
    thread = None
    processes = []

    def run(command):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('25 second command deadline exceeded')
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        processes.append(process)
        try:
            stdout, stderr = process.communicate(timeout=remaining)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired as error:
            # Terminate only the process group created by this harness.
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=1)
            report.update(stdout=stdout, stderr=stderr)
            raise TimeoutError('25 second command deadline exceeded') from error
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    try:
        version_code, version_out, version_err = run([args.chrome, '--version'])
        report.update(browser_version=version_out.strip(), version_stderr=version_err, version_exit_code=version_code)
        if version_code:
            raise RuntimeError('Browser version command failed')
        handler = functools.partial(QuietHandler, directory=str(Path(__file__).resolve().parent))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        with tempfile.TemporaryDirectory(prefix='portable-refresh-browser-') as profile:
            exit_code, stdout, stderr = run([
                args.chrome, '--headless', '--dump-dom', '--no-first-run',
                '--no-default-browser-check', '--user-data-dir=' + profile,
                '--virtual-time-budget=5000',
                f'http://127.0.0.1:{server.server_port}/browser-check.html',
            ])
            report.update(exit_code=exit_code, stdout=stdout, stderr=stderr)
            match = re.search(r'<pre\b(?=[^>]*\bid="result")(?=[^>]*\bdata-status="(pass|fail)")[^>]*>(.*?)</pre>', stdout, re.S)
            if not match:
                raise RuntimeError('Browser did not produce a completed result')
            result = json.loads(html.unescape(match.group(2)))
            report['result'] = result
            report['status'] = 'pass' if exit_code == 0 and match.group(1) == 'pass' and result.get('status') == 'pass' else 'fail'
    except Exception as error:
        report['error'] = str(error)
    finally:
        for process in processes:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=1)
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=1)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['status'] == 'pass' else 1

if __name__ == '__main__':
    raise SystemExit(main())
