import hashlib
import json
import os
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT/'tools/re/rust_source_cli.py'
PIN = 'd49ba1209f4a2545250c34322414b7f92f50435f110220433cfd33e83fc00c31'
PHASES = {19:'source_validated',21:'compiler_identity_validated',23:'snapshot_validated',28:'generated_source_written',30:'compiler_wait_completed',32:'postbuild_identity_validated'}


def main():
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest() == PIN
    output = Path(sys.argv[sys.argv.index('--output')+1])
    assert output.is_absolute() and output.parent.is_dir()
    descriptor = os.open(output.parent/'cli-phases.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    started = time.monotonic()
    seen = set()
    def trace(frame,event,arg):
        if frame.f_code.co_filename != str(TARGET): return None
        if event == 'line' and frame.f_code.co_name == 'main' and frame.f_lineno in PHASES and frame.f_lineno not in seen:
            seen.add(frame.f_lineno)
            row = {'phase':PHASES[frame.f_lineno],'line':frame.f_lineno,'pid':os.getpid(),'elapsed_seconds':time.monotonic()-started,'cli_sha256':PIN}
            payload = (json.dumps(row)+'\n').encode()
            assert len(payload) <= 1024 and os.write(descriptor,payload) == len(payload)
        return trace
    sys.argv[0] = str(TARGET)
    sys.path.insert(0,str(ROOT/'tools/re'))
    sys.settrace(trace)
    try:
        runpy.run_path(str(TARGET),run_name='__main__')
    finally:
        sys.settrace(None)
        os.close(descriptor)


if __name__ == '__main__':
    main()
