import sys,pathlib,json,time,hashlib,subprocess,os
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop import sourcecache
from reloop.libprocobserver import Observer
binary=r/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot'
code='''import os,sys,time,json,pathlib,ctypes
folder=pathlib.Path(sys.argv[1]);mode=sys.argv[2];child=None
if mode=='detached':
 readfd,writefd=os.pipe();child=os.fork()
 if child==0:
  os.close(readfd);parent=os.getppid();os.setsid()
  with (folder/'heartbeat.bin').open('wb',buffering=0) as out:
   for i in range(32):
    out.write(bytes([i]))
    if i==0:os.write(writefd,b'1');os.close(writefd)
    time.sleep(0.05)
  (folder/'child-finished.json').write_text(json.dumps({'pid':os.getpid(),'original_parent':parent,'group':os.getpgrp(),'bytes':32,'self_terminated':True})+'\\n');os._exit(0)
 os.close(writefd);assert os.read(readfd,1)==b'1';os.close(readfd)
system=ctypes.CDLL('/usr/lib/libSystem.B.dylib');f=system._NSGetExecutablePath;f.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];f.restype=ctypes.c_int;n=ctypes.c_uint32(4096);b=ctypes.create_string_buffer(n.value);assert f(b,ctypes.byref(n))==0
row={'pid':os.getpid(),'parent':os.getppid(),'group':os.getpgrp(),'child_pid':child,'executable':str(pathlib.Path(os.fsdecode(b.value)).resolve())};tmp=folder/'ready.tmp';tmp.write_text(json.dumps(row)+'\\n');os.replace(tmp,folder/'ready.json');time.sleep(0.45)
print('owned observed root' if mode=='clean' else json.dumps(row),flush=True)
'''
with Controller().lock():
 e=r/'research/evidence/observer-ready-admission-2026-10-11';e.mkdir();(e/'emitter.py').write_text(code);f=r/'tools/re/fixtures/ObserverReadyAdmission';f.mkdir();(f/'emitter.py').write_text(code)
 for name in ['sourcecache','compilerwitness']:(e/(name+'.py')).write_bytes((r/'tools/re/reloop'/(name+'.py')).read_bytes())
 (e/'prediction.json').write_text(json.dumps({'scope':'Explicit controlled readiness protocol before first live-root snapshot, not generic compiler startup workaround','prediction':'Capture acknowledged root/child identities while rootlive; after actualroot0 reject still-live same-identity detachedchild without destructive signals. Clean acknowledged root admits. Signal denial and ungated startup remain unqualified.','limits':{'producer_roles':3,'observer_samples_per_compiler':64,'snapshot_seconds':2,'ready_seconds':1,'compiler_seconds':3,'child_ticks':32,'child_tick_seconds':0.05,'completion_seconds':3}},indent=2)+'\n')
 observer=Observer(binary);samples=[];signals=[];processes=[];mode=None;folder=None;realpopen=subprocess.Popen;realgroup=os.killpg
 def observed(roots,known):
  start=time.monotonic();ready=None
  if roots:
   deadline=time.monotonic()+1
   while not (folder/'ready.json').exists() and time.monotonic()<deadline:time.sleep(0.01)
   ready=json.loads((folder/'ready.json').read_text());assert roots=={ready['pid']} and ready['parent']==os.getpid() and ready['group']==ready['pid']
  rows=observer.snapshot(roots,known);samples.append({'mode':mode,'roots':sorted(roots),'known':known,'ready':ready,'rows':rows,'elapsed_seconds':time.monotonic()-start});return rows
 def spawned(args,**kwargs):
  process=realpopen(args,**kwargs)
  if kwargs.get('start_new_session'):processes.append(process)
  return process
 def signalled(pid,sig):
  row={'mode':mode,'pid':pid,'signal':sig};signals.append(row)
  try:result=realgroup(pid,sig)
  except ProcessLookupError:row['outcome']='absent';raise
  row['outcome']='present';return result
 results=[]
 for mode in ['detached','clean']:
  folder=e/mode;folder.mkdir();start=time.monotonic();result=None;error=None
  with patch.object(sourcecache.subprocess,'Popen',side_effect=spawned),patch.object(sourcecache.os,'killpg',side_effect=signalled):
   try:result=sourcecache.run_compiler([sys.executable,str(e/'emitter.py'),str(folder),mode],timeout=3,observer=observed)
   except RuntimeError as x:error=str(x)
  row={'mode':mode,'root_pid':processes[-1].pid,'root_exit_code':processes[-1].returncode,'code':None if result is None else result.returncode,'stdout':None if result is None else result.stdout.decode(),'stderr':None if result is None else result.stderr.decode(),'error':error,'elapsed_seconds':time.monotonic()-start}
  if mode=='detached':
   first=(folder/'heartbeat.bin').read_bytes();(folder/'at-rejection.bin').write_bytes(first);time.sleep(0.3);later=(folder/'heartbeat.bin').read_bytes();(folder/'after-rejection.bin').write_bytes(later);end=time.monotonic()+3
   while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
   row.update(first_bytes=len(first),later_bytes=len(later),child_finished=(folder/'child-finished.json').exists())
  (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row);print(mode,row['root_exit_code'],row['code'],error,flush=True)
 (e/'samples.json').write_text(json.dumps(samples,indent=2)+'\n');(e/'signals.json').write_text(json.dumps(signals,indent=2)+'\n');(e/'environment.json').write_text(json.dumps({'observer_binary':str(binary),'observer_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256((r/'tools/re/reloop/libprocobserver.py').read_bytes()).hexdigest(),'observer_subprocesses':len(samples),'native_subprocesses':3+len(samples),'scope':'Existing reviewed explicit backend; staged user observer changes untouched'},indent=2)+'\n');print('observers',len(samples),'signals',signals,flush=True)
