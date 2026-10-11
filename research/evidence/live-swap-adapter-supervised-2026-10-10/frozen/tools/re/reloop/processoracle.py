"""Discriminating owned libproc controls, independent of Canvas semantics."""
import json
import ctypes
import os
import pathlib
import sys
import time
from unittest.mock import patch
from reloop.core import atomic, execute
from reloop.libprocobserver import build


def corpus(out):
    out=pathlib.Path(out); observer,identity=build(out/'helper')
    own=os.getpid(); samples=[]
    # Xcode's Python launcher differs from its running app executable. Ask dyld
    # independently rather than treating sys.executable as kernel identity.
    system=ctypes.CDLL('/usr/lib/libSystem.B.dylib')
    getpath=system._NSGetExecutablePath
    getpath.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
    getpath.restype=ctypes.c_int
    size=ctypes.c_uint32(4096);buffer=ctypes.create_string_buffer(size.value)
    assert getpath(buffer,ctypes.byref(size))==0,'dyld executable path unavailable'
    expected_path=str(pathlib.Path(os.fsdecode(buffer.value)).resolve())
    birth=None
    for _ in range(20):
        start=time.monotonic(); row=observer.snapshot({own})[own]
        samples.append(time.monotonic()-start)
        assert row['parent']==os.getppid() and row['group']==os.getpgid(own)
        assert row['identity'][2]==expected_path,'libproc executable disagrees with dyld'
        if birth is None: birth=row['identity'][:2]
        assert row['identity'][:2]==birth and all(v>=0 for v in birth)
    controls=[]
    # Known detached child must be drained before the wrapper returns.
    folder=out/'detached';folder.mkdir()
    marker=folder/'late'
    child="import os,time,pathlib;os.setsid();time.sleep(1.8);pathlib.Path(%r).write_text('late')" % str(marker)
    parent="import subprocess,time,sys;subprocess.Popen([sys.executable,'-c',%r]);time.sleep(30)" % child
    events=[]
    result=execute([sys.executable,'-c',parent],folder,0.7,1024*1024,lambda k,v:events.append({'event':k,**v}),observer=observer.snapshot)
    assert result['execution']=='timed_out' and result['exit_code'] is not None
    assert any(e['event']=='owned_descendant_cleanup' and e['tracked_processes']>=2 for e in events)
    time.sleep(1.5);assert not marker.exists()
    controls.append({'name':'detached-timeout','result':result,'cleanup_events':events,'late_write_absent':True})
    for name,source,status,exit_code in [('exit-zero','pass','success',0),('exit-nonzero','raise SystemExit(7)','failed',7)]:
        folder=out/name;folder.mkdir()
        result=execute([sys.executable,'-c',source],folder,3,1024*1024,observer=observer.snapshot)
        assert result['execution']==status and result['exit_code']==exit_code
        controls.append({'name':name,'result':result})
    # Reuse/exec controls deliberately falsify known identity for a live owned
    # process. No signal is emitted; kernel PID reuse itself is not claimed.
    from reloop.processes import OwnedTree
    for name,mutate in [('birth',lambda i:(i[0]+1,i[1],i[2])),('executable',lambda i:(i[0],i[1],'/wrong-executable'))]:
        actual=observer.snapshot({own})[own]['identity']
        tree=OwnedTree(2147483647,snapshotter=observer.snapshot);tree.known={own:mutate(actual)}
        real_kill=os.kill
        def read_only_kill(pid,sig):
            if sig==0:return real_kill(pid,0)
            raise AssertionError('Mutation control attempted a destructive signal')
        with patch('reloop.processes.os.kill',side_effect=read_only_kill) as kill:
            tree.drain()
            assert all(call.args[1]==0 for call in kill.call_args_list)
        controls.append({'name':name+'-identity-mutation','signals':0})
    atomic(out/'controls.json',{'helper':identity,'samples_seconds':samples,'controls':controls,
        'scope':'Public libproc owned identity/cleanup control; not native Canvas release or physical reclamation.'})
    return {'stable_samples':20,'independent_parent_group_path':True,'detached_timeout_drained':True,
            'late_write_absent':True,'nonzero_retained':True,'identity_mutations_rejected':2,
            'snapshot_deadline_seconds':2,'maximum_snapshot_seconds':max(samples),
            'scope':'Owned helper only; no actual kernel PID reuse or Canvas policy acceptance.'}
