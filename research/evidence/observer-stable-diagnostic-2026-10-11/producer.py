import sys,pathlib,json,time,hashlib,ctypes,os,subprocess
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.libprocobserver import Observer
binary=r/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot'
code='''import ctypes,os,pathlib,json,sys,time
system=ctypes.CDLL('/usr/lib/libSystem.B.dylib');f=system._NSGetExecutablePath;f.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];f.restype=ctypes.c_int;n=ctypes.c_uint32(4096);b=ctypes.create_string_buffer(n.value);assert f(b,ctypes.byref(n))==0
row={'pid':os.getpid(),'parent':os.getppid(),'group':os.getpgrp(),'uid':os.getuid(),'euid':os.geteuid(),'executable':str(pathlib.Path(os.fsdecode(b.value)).resolve())};folder=pathlib.Path(sys.argv[1]);(folder/'ready.json').write_text(json.dumps(row)+'\\n');time.sleep(1);(folder/'finished.bin').write_bytes(b'finished')
'''
with Controller().lock():
 e=r/'research/evidence/observer-stable-diagnostic-2026-10-11';e.mkdir();(e/'child.py').write_text(code);f=r/'tools/re/fixtures/ObserverStableDiagnostic';f.mkdir();(f/'child.py').write_text(code)
 (e/'prediction.json').write_text(json.dumps({'scope':'Read-only observer on stable caller and acknowledged child, contrasting native compiler startup failure; no signal operations','alternatives':['Stable caller/child observed: earlier failure is phase-specific and not evidence of blanket backend loss.','Stable targets still inaccessible: observer availability is broader prerequisite.','Popen root differs from independently acknowledged program PID: do not conflate launcher and running process.'],'limits':{'child_producers':1,'observer_subprocesses':4,'snapshot_seconds':2,'child_self_exit_seconds':1,'ready_seconds':2,'root_wait_seconds':2}},indent=2)+'\n')
 observer=Observer(binary);system=ctypes.CDLL('/usr/lib/libSystem.B.dylib');getpath=system._NSGetExecutablePath;getpath.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];getpath.restype=ctypes.c_int;size=ctypes.c_uint32(4096);buf=ctypes.create_string_buffer(size.value);assert getpath(buf,ctypes.byref(size))==0
 own={'pid':os.getpid(),'parent':os.getppid(),'group':os.getpgrp(),'uid':os.getuid(),'euid':os.geteuid(),'executable':str(pathlib.Path(os.fsdecode(buf.value)).resolve())};samples=[]
 def sample(label,target,expected):
  start=time.monotonic();rows=None;error=None
  try:rows=observer.snapshot({target})
  except Exception as x:error={'type':type(x).__name__,'message':str(x)}
  samples.append({'label':label,'target':target,'expected':expected,'rows':rows,'error':error,'elapsed_seconds':time.monotonic()-start});return rows
 for i in range(2):sample('caller-'+str(i),own['pid'],own);time.sleep(0.05)
 folder=e/'child';folder.mkdir();child=subprocess.Popen([sys.executable,str(e/'child.py'),str(folder)],start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);deadline=time.monotonic()+2
 while not (folder/'ready.json').exists() and time.monotonic()<deadline:time.sleep(0.01)
 ready=json.loads((folder/'ready.json').read_text());spawn={'popen_pid':child.pid,'controller_pid':os.getpid(),'popen_group':os.getpgid(child.pid),'ready':ready}
 for i in range(2):
  if child.poll() is not None:break
  sample('child-'+str(i),child.pid,ready);time.sleep(0.05)
 out,err=child.communicate(timeout=2);(e/'wait.json').write_text(json.dumps({'spawn':spawn,'code':child.returncode,'stdout':out.decode(),'stderr':err.decode(),'finished_bytes':(folder/'finished.bin').stat().st_size},indent=2)+'\n');(e/'samples.json').write_text(json.dumps(samples,indent=2)+'\n');(e/'environment.json').write_text(json.dumps({'observer_binary':str(binary),'observer_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256((r/'tools/re/reloop/libprocobserver.py').read_bytes()).hexdigest(),'observer_subprocesses':len(samples),'signal_operations':0,'scope':'Owned selected lifetime/parent/group/path; no arguments, user process mutations or native compiler retry'},indent=2)+'\n')
 for row in samples:print(row['label'],'target',row['target'],'rows',list(row['rows'] or {}),'error',row['error'],flush=True)
 print('popen/ready',child.pid,ready['pid'],'caller/parent',own['pid'],ready['parent'],'wait',child.returncode,flush=True)
