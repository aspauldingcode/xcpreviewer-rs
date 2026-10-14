#!/Users/8amps/xcpreviewer-rs/research/venv/bin/python
import hashlib
import json
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANCHOR = ROOT/'tools/re/reloop/observed_group_anchor.py'
PIN = '48c73a15ac5720ec653271bc6ec523a090fb2bff4301f2308a9812faea4187b8'


def main():
    if Path(sys.argv[1]) != ANCHOR:
        assert Path(sys.argv[1]) == ROOT/'tools/re/tests/owned_cli_phase_optimized_wrapper.py'
        os.execv(sys.executable,[sys.executable,*sys.argv[1:]])
    assert hashlib.sha256(ANCHOR.read_bytes()).hexdigest() == PIN
    sys.argv = sys.argv[1:]
    output = Path(sys.argv[-1])/'result'
    delayed = output.parent.name in ['delayed-zero','delayed-failure']
    deadline_value = None
    terminal_before_deadline = None
    delay_applied = False
    descriptor = os.open(output.parent/'deadline-audit.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    original_clock = time.monotonic
    original_process = subprocess.Popen
    target_command = sys.argv[4:]
    count = 0
    def emit(row):
        nonlocal count
        count += 1
        if count > 512: return
        row['sequence'] = count
        payload = (json.dumps(row)+'\n').encode()
        assert len(payload) <= 1024 and os.write(descriptor,payload) == len(payload)
    def clock():
        nonlocal deadline_value, delay_applied
        frame = sys._getframe(1)
        if delayed and not delay_applied and terminal_before_deadline is not None and frame.f_code.co_filename == str(ANCHOR) and frame.f_lineno == 110:
            delay_applied = True
            before = original_clock()
            emit({'kind':'injected_delay_start','value':before,'terminal_observed_at':terminal_before_deadline,'deadline':deadline_value})
            time.sleep(max(0,deadline_value+0.05-before))
            emit({'kind':'injected_delay_end','value':original_clock()})
        value = original_clock()
        if frame.f_code.co_filename == str(ANCHOR) and frame.f_lineno == 45: deadline_value = value+int(sys.argv[3])/1000
        if frame.f_code.co_filename == str(ANCHOR):
            emit({'kind':'anchor_clock','line':frame.f_lineno,'value':value,'anchor_pid':os.getpid()})
        return value
    class Process(original_process):
        def __init__(self, command, *args, **kwargs):
            self.owned_target = command == target_command
            super().__init__(command,*args,**kwargs)
            if self.owned_target: emit({'kind':'target_spawn','pid':self.pid,'anchor_pid':os.getpid(),'value':original_clock()})
        def poll(self):
            nonlocal terminal_before_deadline
            code = super().poll()
            if self.owned_target and code is not None and original_clock() < deadline_value and terminal_before_deadline is None: terminal_before_deadline = original_clock()
            if self.owned_target: emit({'kind':'target_poll','pid':self.pid,'code':code,'value':original_clock()})
            return code
    sys.path.insert(0,str(ROOT/'tools/re'))
    namespace = runpy.run_path(str(ANCHOR),run_name='owned_deadline_audit_load')
    emit({'kind':'audit_identity','anchor_sha256':PIN,'milliseconds':int(sys.argv[3]),'clock_implementation':time.get_clock_info('monotonic').implementation})
    subprocess.Popen = Process
    time.monotonic = clock
    try:
        namespace['main']()
    finally:
        subprocess.Popen = original_process
        time.monotonic = original_clock
        os.close(descriptor)


if __name__ == '__main__':
    main()
