import sys,pathlib,json,time,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.sourcecache import run_compiler
with Controller().lock():
 e=r/'research/evidence/compiler-success-descendant-2026-10-11';assert (e/'repeat-0/child-finished.json').exists();(e/'harness-failure.json').write_text(json.dumps({'phase':'repeat-0','failure':'TypeError: cannot unpack non-iterable CompletedProcess object','producer_ran':True,'root_return_not_retained':True,'at_return_snapshot_absent':True,'child_finished':True,'process_budget_used':2,'repeat_retry':False},indent=2)+'\n');(e/'failed-producer.py').write_bytes(pathlib.Path('/private/tmp/success-descendant-run.py').read_bytes())
 folder=e/'repeat-1';folder.mkdir();started=time.monotonic();result=run_compiler([sys.executable,str(e/'emitter.py'),str(folder)],timeout=3);elapsed=time.monotonic()-started;first=(folder/'heartbeat.bin').read_bytes();(folder/'at-return.bin').write_bytes(first);time.sleep(0.3);second=(folder/'heartbeat.bin').read_bytes();(folder/'after-return.bin').write_bytes(second)
 end=time.monotonic()+3
 while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
 finished=(folder/'child-finished.json').exists();final=(folder/'heartbeat.bin').read_bytes();(folder/'wait.json').write_text(json.dumps({'root_code':result.returncode,'root_elapsed_seconds':elapsed,'root_stdout':result.stdout.decode(),'root_stderr':result.stderr.decode(),'child_finished_within_bound':finished,'first_bytes':len(first),'later_bytes':len(second),'final_bytes':len(final)},indent=2)+'\n');print(result.returncode,elapsed,len(first),len(second),len(final),finished,flush=True)
 (e/'environment.json').write_text(json.dumps({'python':sys.executable,'python_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),'platform':sys.platform,'sourcecache_sha256':hashlib.sha256((e/'sourcecache.py').read_bytes()).hexdigest(),'scope':'Owned source-level compiler boundary, not shipped binary reconstruction'},indent=2)+'\n')
