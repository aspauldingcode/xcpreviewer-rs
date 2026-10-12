import sys,pathlib,json,hashlib,time,shutil
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.sourcecache import run_compiler
code=r'''import os,sys,time,json,pathlib
folder=pathlib.Path(sys.argv[1]);readfd,writefd=os.pipe();child=os.fork()
if child==0:
 os.close(readfd);owner=os.getppid();group=os.getpgrp()
 with (folder/'heartbeat.bin').open('wb',buffering=0) as output:
  for i in range(24):
   output.write(bytes([i]));
   if i==0:os.write(writefd,b'1');os.close(writefd)
   time.sleep(0.05)
 (folder/'child-finished.json').write_text(json.dumps({'pid':os.getpid(),'original_parent':owner,'process_group':group,'bytes':24,'self_terminated':True})+'\n');os._exit(0)
os.close(writefd);assert os.read(readfd,1)==b'1';os.close(readfd)
print(json.dumps({'pid':os.getpid(),'child_pid':child,'process_group':os.getpgrp(),'owns_child':True}),flush=True)
'''
with Controller().lock():
 e=r/'research/evidence/compiler-success-descendant-2026-10-11';e.mkdir();(e/'emitter.py').write_text(code);f=r/'tools/re/fixtures/CompilerSuccessDescendant';f.mkdir();(f/'emitter.py').write_text(code)
 (e/'prediction.json').write_text(json.dumps({'scope':'Actual sourcecache run_compiler normal exit with a finite owned same-group child writing controlled bytes; not artifact publication or arbitrary compiler tree','alternatives':['run_compiler success waits for owned child quiescence','run_compiler returns root0 while child continues writing'],'limits':{'producer_processes':4,'run_compiler_timeout_seconds':3,'child_ticks':24,'child_tick_seconds':0.05,'finish_wait_seconds':3},'cleanup':'Children self-terminate after finite24ticks; no process kill and no user process access.'},indent=2)+'\n')
 (e/'sourcecache.py').write_bytes((r/'tools/re/reloop/sourcecache.py').read_bytes())
 for n in ['repeat-0','repeat-1']:
  folder=e/n;folder.mkdir();started=time.monotonic();code,out,err=run_compiler([sys.executable,str(e/'emitter.py'),str(folder)],timeout=3);elapsed=time.monotonic()-started;row=json.loads(out);first=(folder/'heartbeat.bin').read_bytes();(folder/'at-return.bin').write_bytes(first);time.sleep(0.3);second=(folder/'heartbeat.bin').read_bytes();(folder/'after-return.bin').write_bytes(second)
  end=time.monotonic()+3
  while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
  finished=(folder/'child-finished.json').exists();final=(folder/'heartbeat.bin').read_bytes();(folder/'wait.json').write_text(json.dumps({'root_code':code,'root_elapsed_seconds':elapsed,'root_stdout':out.decode(),'root_stderr':err.decode(),'child_finished_within_bound':finished,'first_bytes':len(first),'later_bytes':len(second),'final_bytes':len(final)},indent=2)+'\n');print(n,code,elapsed,len(first),len(second),len(final),finished,flush=True)
 (e/'environment.json').write_text(json.dumps({'python':sys.executable,'python_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),'platform':sys.platform,'sourcecache_sha256':hashlib.sha256((e/'sourcecache.py').read_bytes()).hexdigest(),'scope':'Owned source-level compiler boundary, not shipped binary reconstruction'},indent=2)+'\n')
