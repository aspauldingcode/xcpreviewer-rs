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


def main():
    helper, expected, milliseconds = sys.argv[1:4]
    known = {}; topology = {}; target = None; observations = 0; failure = None
    os.set_blocking(0, False)
    deadline = time.monotonic()+int(milliseconds)/1000

    def emit(value):
        os.write(3, (json.dumps(value)+'\n').encode())

    def snapshot():
        nonlocal observations
        assert hashlib.sha256(open(helper,'rb').read()).hexdigest() == expected
        roots = [str(target.pid)] if target.poll() is None else []
        args = roots+['%d:%d:%d' % (pid,*ident[:2]) for pid,ident in known.items()]
        data = subprocess.run([helper,*args],capture_output=True,check=True,timeout=1)
        assert len(data.stdout) <= 1048576
        assert hashlib.sha256(open(helper,'rb').read()).hexdigest() == expected
        rows = {}
        for row in json.loads(data.stdout):
            pid = row['pid']; ident = row['identity']
            assert type(pid) is int and pid>0 and pid not in rows
            assert len(ident)==3 and all(type(v) is int and v>=0 for v in ident[:2])
            assert isinstance(ident[2],str) and ident[2].startswith('/')
            ident[2]=os.fsdecode(ident[2].encode('latin1'));row['identity']=tuple(ident)
            assert row['state'] in ('L','Z') and type(row['parent']) is int
            rows[pid]=row
        if roots and target.pid not in rows and target.poll() is None:
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
            if time.monotonic()>=deadline:failure='deadline';break
            if target.poll() is not None:break
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
