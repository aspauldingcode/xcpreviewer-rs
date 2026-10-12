import sys,pathlib,json,hashlib,time
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.sourcecache import run_compiler
from reloop.libprocobserver import Observer
binary=r/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot'
with Controller().lock():
 e=r/'research/evidence/compiler-observed-admission-2026-10-11';observer=Observer(binary);samples=[]
 def observed(roots,known):
  start=time.monotonic();rows=observer.snapshot(roots,known);samples.append({'roots':sorted(roots),'known':known,'rows':rows,'elapsed_seconds':time.monotonic()-start});return rows
 for name in ['group-only','observed']:
  folder=e/name;folder.mkdir();started=time.monotonic();result=None;error=None
  try:result=run_compiler([sys.executable,str(e/'emitter.py'),str(folder)],timeout=3,**({'observer':observed} if name=='observed' else {}))
  except RuntimeError as x:error=str(x)
  elapsed=time.monotonic()-started;first=(folder/'heartbeat.bin').read_bytes();(folder/'at-return.bin').write_bytes(first);time.sleep(0.3);later=(folder/'heartbeat.bin').read_bytes();(folder/'after-return.bin').write_bytes(later);end=time.monotonic()+3
  while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
  (folder/'result.json').write_text(json.dumps({'code':None if result is None else result.returncode,'stdout':None if result is None else result.stdout.decode(),'stderr':None if result is None else result.stderr.decode(),'error':error,'elapsed_seconds':elapsed,'first_bytes':len(first),'later_bytes':len(later),'finished':(folder/'child-finished.json').exists(),'destructive_success_signal':False},indent=2)+'\n');print(name,None if result is None else result.returncode,error,len(first),len(later),flush=True)
 (e/'observer-samples.json').write_text(json.dumps(samples,indent=2)+'\n');(e/'environment.json').write_text(json.dumps({'observer_binary':str(binary),'observer_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'observer_adapter':str(r/'tools/re/reloop/libprocobserver.py'),'observer_adapter_sha256':hashlib.sha256((r/'tools/re/reloop/libprocobserver.py').read_bytes()).hexdigest(),'observer_source_sha256':hashlib.sha256((r/'tools/re/native/OwnedProcessSnapshot.c').read_bytes()).hexdigest(),'observer_samples':len(samples),'total_native_processes':4+len(samples),'scope':'Explicit existing reviewed public libproc backend; staged user backend is not committed or selected by default'},indent=2)+'\n')
