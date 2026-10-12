import sys,pathlib,json,hashlib,time,subprocess,os
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop import sourcecache
from reloop.libprocobserver import Observer
from reloop.primarysource import expression
from reloop.portable import TOOLCHAIN
binary=r/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot'
with Controller().lock():
 e=r/'research/evidence/compiler-observer-qualification-2026-10-11';e.mkdir();(e/'prediction.json').write_text(json.dumps({'scope':'Changed root-exec refresh: actual post-root rejection of observed detached child plus real cold/cache-hit WASM with explicit observer','prediction':'Observe child while root live, retain full identity through setsid/reparenting, actual root0 then reject known live child without new destructive success signals. Two real LLVM cold stages admit; same source cache hit starts no compiler or observer calls. WASM binary identity compared to independently verified previous build, no fresh runtime execution.','limits':{'root_producer_roles':4,'compiler_deadline_seconds':3,'LLVM_deadline_seconds':30,'observer_samples_per_compiler':64,'observer_subprocess_deadline_seconds':2,'child_ticks':32,'child_tick_seconds':0.05,'finish_wait_seconds':3}},indent=2)+'\n')
 for n in ['sourcecache','compilerwitness']:(e/(n+'.py')).write_bytes((r/'tools/re/reloop'/(n+'.py')).read_bytes())
 (e/'emitter.py').write_bytes((r/'tools/re/fixtures/CompilerObservedAdmission/emitter.py').read_bytes());observer=Observer(binary);samples=[];spawns=[];signals=[];phase='detached';realpopen=subprocess.Popen;realgroup=os.killpg
 def observed(roots,known):
  start=time.monotonic();rows=observer.snapshot(roots,known);samples.append({'phase':phase,'roots':sorted(roots),'known':known,'rows':rows,'elapsed_seconds':time.monotonic()-start});return rows
 def spawned(args,**kwargs):
  process=realpopen(args,**kwargs)
  if kwargs.get('start_new_session'):
   spawns.append({'process':process,'argv':args,'pid':process.pid,'group':os.getpgid(process.pid),'phase':phase,'start_new_session':True})
  return process
 def group_signal(pid,sig):
  row={'pid':pid,'signal':sig,'phase':phase};signals.append(row)
  try:result=realgroup(pid,sig)
  except ProcessLookupError:row['outcome']='absent';raise
  row['outcome']='present';return result
 folder=e/'detached';folder.mkdir();start=time.monotonic();error=None
 with patch.object(sourcecache.subprocess,'Popen',side_effect=spawned),patch.object(sourcecache.os,'killpg',side_effect=group_signal):
  try:sourcecache.run_compiler([sys.executable,str(e/'emitter.py'),str(folder)],timeout=3,observer=observed)
  except RuntimeError as x:error=str(x)
 elapsed=time.monotonic()-start;root_code=spawns[0]['process'].returncode;first=(folder/'heartbeat.bin').read_bytes();(folder/'at-rejection.bin').write_bytes(first);time.sleep(0.3);later=(folder/'heartbeat.bin').read_bytes();(folder/'after-rejection.bin').write_bytes(later);end=time.monotonic()+3
 while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
 (folder/'result.json').write_text(json.dumps({'root_exit_code':root_code,'error':error,'elapsed_seconds':elapsed,'first_bytes':len(first),'later_bytes':len(later),'child_finished':(folder/'child-finished.json').exists(),'post_fix':True},indent=2)+'\n');print('detached',root_code,error,len(first),len(later),flush=True)
 phase='cold';text=expression(12);(e/'input.swift').write_text(text)
 with patch.object(sourcecache.subprocess,'Popen',side_effect=spawned),patch.object(sourcecache.os,'killpg',side_effect=group_signal):
  cold=sourcecache.build(text,e/'cache',e/'output',TOOLCHAIN/'clang',TOOLCHAIN/'wasm-ld',compiler_observer=observed);before=(e/'output/current.json').read_bytes();calls_before=len(spawns);samples_before=len(samples);phase='hit';hit=sourcecache.build(text,e/'cache',e/'output',TOOLCHAIN/'clang',TOOLCHAIN/'wasm-ld',compiler_observer=observed)
 (e/'build.json').write_text(json.dumps({'cold':cold,'hit':hit,'pointer_hex':before.hex(),'spawns_before_hit':calls_before,'spawns_after_hit':len(spawns),'samples_before_hit':samples_before,'samples_after_hit':len(samples)},indent=2)+'\n')
 rows=[]
 for row in spawns:row=dict(row);process=row.pop('process');row['code']=process.returncode;rows.append(row)
 (e/'spawns.json').write_text(json.dumps(rows,indent=2)+'\n');(e/'signals.json').write_text(json.dumps(signals,indent=2)+'\n');(e/'observer-samples.json').write_text(json.dumps(samples,indent=2)+'\n');(e/'environment.json').write_text(json.dumps({'observer_binary':str(binary),'observer_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'observer_adapter_sha256':hashlib.sha256((r/'tools/re/reloop/libprocobserver.py').read_bytes()).hexdigest(),'observer_subprocesses':len(samples),'tools':{n:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in [('clang',TOOLCHAIN/'clang'),('wasm_ld',TOOLCHAIN/'wasm-ld')]},'scope':'Existing explicit reviewed libproc backend; user staged backend remains uncommitted'},indent=2)+'\n');print('cold/hit',cold['cache_hit'],hit['cache_hit'],'module',cold['module_sha256'],'observers',len(samples),'signals',signals,flush=True)
