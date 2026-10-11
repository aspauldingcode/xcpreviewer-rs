#!/usr/bin/env python3
"""Exclusive, frozen, bounded standalone live-swap adapter; graph binding pending."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys


def execute_owned(argv, stdout, stderr, environment, seconds):
    """Only the new owned session receives timeout cleanup; no external PID lookup."""
    process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=environment,
                               start_new_session=True)
    try:
        code = process.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        raise
    if code:
        raise subprocess.CalledProcessError(code, argv)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        from reloop.liveswapprobe import corpus
        print(json.dumps(corpus(args.out)))
        return
    project = Path(__file__).resolve().parents[2]
    with (project / 'research/state/controller.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
        frozen = out / 'frozen/tools/re'
        shutil.copytree(project / 'tools/re', frozen, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        environment = {**os.environ, 'RE_PROJECT_ROOT': str(project)}
        error = None
        try:
            with (out / 'worker.stdout').open('wb') as stdout, (out / 'worker.stderr').open('wb') as stderr:
                execute_owned([sys.executable, str(frozen / 'live-swap-probe.py'), '--worker', '--out', str(out)],
                              stdout, stderr, environment, 90)
        except Exception as exception:
            error = str(exception)
        files = [{'path': str(f.relative_to(out)), 'bytes': f.stat().st_size,
                  'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
                 for f in sorted(out.rglob('*')) if f.is_file()]
        manifest = {'version': 1, 'execution': 'failed' if error else 'success',
                    'error': error, 'scientific_delivery_review': 'pending',
                    'scope': 'Frozen consolidated adapter, owned policy only; graph binding pending', 'files': files}
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps({'execution': manifest['execution'], 'manifest_sha256': hashlib.sha256((out / 'manifest.json').read_bytes()).hexdigest()}))
        if error:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
