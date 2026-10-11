"""Owned setsid/reparenting control; observation precedes target retirement.

The group-only arm intentionally allows its naturally bounded child to finish.
The observed arm uses the explicit public libproc backend and full identities.
No existing application, arbitrary PID, or unseen escaped child is targeted.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/re'))
from reloop.core import Controller, PROJECT_ROOT, atomic, digest
from reloop.libprocobserver import build
from reloop.processes import OwnedTree

TARGET = '''import json,os,pathlib,sys,time
folder=pathlib.Path(sys.argv[1]); code=int(sys.argv[2])
child=os.fork()
if child==0:
 os.setsid()
 (folder/'ready.json').write_text(json.dumps({'child':os.getpid(),'parent':os.getppid(),'group':os.getpgrp()}))
 deadline=time.monotonic()+4
 while not (folder/'release').exists() and time.monotonic()<deadline:time.sleep(.01)
 time.sleep(1.2)
 (folder/'late').write_text('late')
 os._exit(0)
deadline=time.monotonic()+4
while not (folder/'release').exists() and time.monotonic()<deadline:time.sleep(.01)
(folder/'exiting').write_text(str(os.getpid()))
os._exit(code)
'''
NODE = '''const fs=require('node:fs'),{runOwned}=require(process.argv[2]);
(async()=>{let record,error=null;try{record=await runOwned(process.argv[3],[process.argv[4],process.argv[5],process.argv[6]],{supervisorPython:process.argv[3],timeout:3000});}catch(e){record=e.record;error=String(e);}
fs.writeFileSync(process.argv[5]+'/node-result.json',JSON.stringify({record,error}));})();
'''


def wait_file(path, timeout=3):
    deadline = time.monotonic()+timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(str(path))
        time.sleep(.01)


def corpus(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    observer, tool = build(out/'helper')
    atomic(out/'predictions.json', {
        'group_only': 'setsid child survives target/anchor retirement and writes late',
        'observed': 'same full identity survives reparenting; drain prevents late write',
        'mutants': 'birth seconds, microseconds, executable mismatches receive no signal',
        'scope': 'explicit observed owned ancestry only; no native Canvas claim'})
    (out/'target.py').write_text(TARGET); (out/'runner.js').write_text(NODE)
    controls = []
    for observed in (False, True):
        for code in (0, 7):
            folder = out/('%s-%d' % ('observed' if observed else 'group', code))
            folder.mkdir()
            argv = [shutil.which('node'), str(out/'runner.js'),
                    str(ROOT/'tools/re/reloop/owned_compiler.js'), sys.executable,
                    str(out/'target.py'), str(folder), str(code)]
            with (folder/'stdout').open('wb') as stdout, (folder/'stderr').open('wb') as stderr:
                proc = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
                tree = OwnedTree(proc.pid, proc, snapshotter=observer.snapshot)
                try:
                    wait_file(folder/'ready.json')
                    ready = json.loads((folder/'ready.json').read_text())
                    rows = tree.observe(); child = ready['child']
                    assert child in tree.known and rows[child]['parent'] == ready['parent']
                    identity = tree.known[child]
                    assert rows[child]['group'] == child
                    (folder/'release').write_text('release')
                    wait_file(folder/'exiting')
                    deadline = time.monotonic()+2
                    while True:
                        after = tree.observe()
                        if child in after and after[child]['parent'] != ready['parent']:
                            break
                        if time.monotonic() >= deadline:
                            raise TimeoutError('Owned child did not reparent')
                        time.sleep(.01)
                    assert after[child]['identity'] == identity
                    cleanup = tree.drain() if observed else None
                    proc.wait(timeout=5)
                    time.sleep(1.3 if observed else .05)
                    result = json.loads((folder/'node-result.json').read_text())
                    assert result['record']['code'] == code
                    assert (result['error'] is None) == (code == 0)
                    late = (folder/'late').exists()
                    assert late is (not observed)
                    controls.append({'observed':observed,'code':code,'identity':identity,
                                     'child':child,'parent_before':ready['parent'],
                                     'parent_after':after[child]['parent'],
                                     'group_after':after[child]['group'],
                                     'late_write':late,'target_status':result,
                                     'cleanup':cleanup})
                finally:
                    if proc.poll() is None:
                        # This is the newly created Node group, never a prior PID.
                        os.killpg(proc.pid, 9)
                        proc.wait(timeout=5)
                    tree.drain()
    # Mutants exercise the signal gate without sending any real signal.
    signals = []; mutants = []
    pid = controls[-1]['child']; original = tuple(controls[-1]['identity'])
    for field in range(3):
        changed = list(original)
        changed[field] = changed[field]+1 if field < 2 else changed[field]+'-changed'
        rows = {pid:{'identity':tuple(changed),'parent':1,'group':pid,'state':'L'}}
        tree = OwnedTree(2147483647, snapshotter=lambda roots, known:rows)
        tree.known = {2147483647:(0,0,'/owned-root'),pid:original}
        with patch('reloop.processes.os.kill', side_effect=lambda p,s:signals.append([p,s])):
            tree.drain()
        mutants.append({'field':field,'no_signal':not signals})
    assert not signals
    result = {'schema_version':1,'controls':controls,'identity_mutants':mutants,
              'tool':tool,'python_sha256':digest(sys.executable),
              'node_sha256':digest(shutil.which('node')),
              'scope':'Observed owned ancestry only; setsid children unseen between snapshots remain excluded.'}
    atomic(out/'result.json', result)
    return result


if __name__ == '__main__':
    with Controller(PROJECT_ROOT).lock():
        result = corpus(sys.argv[1])
    print(json.dumps({'controls':len(result['controls']),'mutants':len(result['identity_mutants'])}))
