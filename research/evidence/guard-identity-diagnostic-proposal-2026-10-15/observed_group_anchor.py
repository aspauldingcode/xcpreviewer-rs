"""Explicit public observer for newly owned targets; never attach to existing roots.

Sampled ancestry and complete birth/executable identities are the signal gate.
Unseen escapes and the observation-to-signal race remain excluded.
"""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time


def parse_snapshot(data):
    """Validate the whole helper response before any identity is eligible to signal.

    This schema check cannot attest that a compromised helper tells the truth.
    Birth microseconds and process IDs follow the public libproc representation.
    """
    values = json.loads(data)
    assert isinstance(values, list) and len(values) <= 256
    rows = {}
    for row in values:
        assert isinstance(row, dict)
        assert set(row) == {'pid', 'parent', 'group', 'state', 'identity'}
        pid = row['pid']; ident = row['identity']
        assert type(pid) is int and 0 < pid <= 2147483647 and pid not in rows
        assert type(row['parent']) is int and 0 <= row['parent'] <= 2147483647
        assert type(row['group']) is int and 0 < row['group'] <= 2147483647
        assert row['state'] in ('L', 'Z')
        assert isinstance(ident, list) and len(ident) == 3
        assert type(ident[0]) is int and 0 <= ident[0] <= 9223372036854775807
        assert type(ident[1]) is int and 0 <= ident[1] < 1000000
        assert isinstance(ident[2], str) and ident[2].startswith('/') and '\0' not in ident[2]
        raw = ident[2].encode('latin1'); assert len(raw) <= 4096
        rows[pid] = dict(row, identity=(ident[0], ident[1], os.fsdecode(raw)))
    return rows


def main():
    helper, expected, milliseconds = sys.argv[1:4]
    known = {}; topology = {}; target = None; observations = 0; failure = None
    os.set_blocking(0, False)
    deadline = time.monotonic()+int(milliseconds)/1000
    completion_before_deadline = False

    def emit(value):
        os.write(3, (json.dumps(value)+'\n').encode())

    def poll_target():
        nonlocal completion_before_deadline
        code = target.poll()
        if code is not None and time.monotonic() < deadline:
            completion_before_deadline = True
        return code

    def snapshot():
        nonlocal observations
        assert hashlib.sha256(open(helper,'rb').read()).hexdigest() == expected
        observed_at = time.monotonic()
        poll_before = poll_target()
        roots = [str(target.pid)] if poll_before is None else []
        args = roots+['%d:%d:%d' % (pid,*ident[:2]) for pid,ident in known.items()]
        data = subprocess.run([helper,*args],capture_output=True,check=True,timeout=1)
        assert len(data.stdout) <= 1048576
        assert hashlib.sha256(open(helper,'rb').read()).hexdigest() == expected
        rows = parse_snapshot(data.stdout)
        poll_after = poll_target() if roots and target.pid not in rows else None
        if roots and target.pid not in rows and poll_after is None:
            diagnostic = {'kind':'missing_live_target_identity',
                          'at_monotonic':time.monotonic(), 'observation_started':observed_at,
                          'helper_args':args, 'target_pid':target.pid,
                          'poll_before':poll_before, 'poll_after':poll_after,
                          'known_target_identity':known.get(target.pid),
                          'known_count':len(known), 'returned_count':len(rows),
                          'observations':observations,
                          'helper_stdout_bytes':len(data.stdout),
                          'helper_stdout_prefix':data.stdout[:32768].decode('utf-8',errors='replace'),
                          'helper_stdout_complete':len(data.stdout)<=32768,
                          'helper_stdout_sha256':hashlib.sha256(data.stdout).hexdigest()}
            encoded = (json.dumps(diagnostic)+'\n').encode()
            assert len(encoded) <= 262144
            os.write(2, encoded)
            raise RuntimeError('Live owned target identity unavailable')
        selected = {target.pid} if roots else set()
        selected.update(pid for pid,ident in known.items() if pid in rows and rows[pid]['identity']==ident)
        while True:
            children={pid for pid,row in rows.items() if row['parent'] in selected}
            if children<=selected:break
            selected.update(children)
        assert len(selected)<=256
        fresh=[]
        for pid in selected:
            if pid in rows:
                shape=(rows[pid]['parent'],rows[pid]['group'])
                if pid not in known or topology.get(pid)!=shape:fresh.append(rows[pid])
                topology[pid]=shape
                known[pid]=rows[pid]['identity']
        observations+=1
        if fresh:emit({'kind':'observed','rows':fresh})
        return rows

    def drain():
        for sig in (signal.SIGTERM,signal.SIGKILL):
            rows=snapshot()
            for pid,ident in list(known.items()):
                if pid in rows and rows[pid]['identity']==ident and rows[pid]['state']!='Z':
                    try:os.kill(pid,sig)
                    except ProcessLookupError:pass
            time.sleep(.05)
        rows=snapshot()
        live=[pid for pid,ident in known.items() if pid in rows and rows[pid]['identity']==ident and rows[pid]['state']!='Z']
        assert not live,'Observed descendants remain live'

    try:
        assert os.path.isabs(helper) and not os.path.islink(helper)
        assert hashlib.sha256(open(helper,'rb').read()).hexdigest()==expected
        target=subprocess.Popen(sys.argv[4:],close_fds=True,stdin=subprocess.DEVNULL)
        while True:
            snapshot()
            try:command=os.read(0,64)
            except BlockingIOError:command=b''
            if command:
                assert command==b'abort\n';failure='abort';break
            code = poll_target()
            if time.monotonic()>=deadline and not completion_before_deadline:failure='deadline';break
            if code is not None:break
            time.sleep(.025)
        # Capture the actual target wait status after bounded observed drain.
        drain();code=target.wait(timeout=1)
        emit({'kind':'complete','target_code':code,'failure':failure,'drained':True,
              'tracked':len(known),'observations':observations,'remaining_observed':0,
              'scope':'Observed full-identity ancestry and inherited group only; unseen escapes excluded'})
    except Exception as error:
        emit({'kind':'complete','target_code':target.poll() if target else None,
              'failure':type(error).__name__+': '+str(error),'drained':False})
    # Creator kills this still-live inherited group only after consuming receipt.
    while True:time.sleep(3600)


if __name__=='__main__':main()
