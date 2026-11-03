"""Actual deletion/restoration of guarded owned source; no UI or synthetic event."""
from pathlib import Path
import argparse,json,subprocess,hashlib,threading,time,fcntl,frida
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pid',type=int,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);root=Path(__file__).resolve().parents[3];source=a.source.resolve()
for n in ['agent.js','session.py']:(r/n).write_bytes(Path(__file__).with_name(n).read_bytes())
mutex=threading.Lock();ready=threading.Event();removed=threading.Event();acks={};script=None;session=None;before=None;deleted=False;failed=False

def emit(**v):
 v['time_ns']=time.monotonic_ns()
 with mutex:
  with (r/'events.jsonl').open('a') as f:f.write(json.dumps(v)+'\n')
def bounded(seconds,call):
 c=frida.Cancellable();t=threading.Timer(seconds,c.cancel);t.start()
 try:
  with c:return call()
 finally:t.cancel()
def message(m,data):
 emit(stage='script',message=m);v=m.get('payload',{})
 if v.get('event')=='hooks-ready':ready.set()
 if v.get('event')=='workspace-removed-enter':removed.set()
 if v.get('event') in ['phase-ack','cleanup-done'] and v['label'] in acks:acks[v['label']].set()
def phase(label,cleanup=False):
 acks[label]=threading.Event();bounded(3,lambda:script.post({'type':'command','payload':{'label':label,'cleanup':cleanup}}));assert acks[label].wait(3),'phase deadline '+label
with open(root/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  assert subprocess.check_output(['ps','-p',str(a.pid),'-o','comm='],timeout=3).decode().strip()=='/Applications/Xcode.app/Contents/MacOS/Xcode'
  for path,digest in [('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode','ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'),('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsScenes.framework/Versions/A/PreviewsScenes','e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09')]:
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
  assert source.is_relative_to(root/'research/build/preview-workspaces') and source.name=='PreviewLab.swift'
  before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  (r/'source-before.swift').write_bytes(before)
  session=bounded(8,lambda:frida.get_local_device().attach(a.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded(8,script.load);assert ready.wait(2)
  phase('baseline');time.sleep(2);assert source.read_bytes()==before
  phase('removed');source.unlink();deleted=True;emit(stage='source-deleted',absent=not source.exists());observed=removed.wait(8);emit(stage='removed-wait-ended',workspace_removed_observed=observed);time.sleep(1)
  phase('restored');assert not source.exists(),'Concurrent source recreation';source.write_bytes(before);deleted=False;emit(stage='source-restored',sha256=hashlib.sha256(source.read_bytes()).hexdigest());time.sleep(3)
 except Exception as e:failed=True;emit(stage='failure',kind=type(e).__name__,error=str(e))
 finally:
  if deleted:
   if not source.exists():source.write_bytes(before);emit(stage='source-restored-finally')
   else:emit(stage='restore-skipped-concurrent-recreation')
  if script and ready.is_set():
   try:phase('cleanup',True)
   except Exception as e:failed=True;emit(stage='cleanup-unconfirmed',error=str(e))
  if script:
   try:bounded(3,script.unload);emit(stage='script-unloaded')
   except Exception as e:failed=True;emit(stage='unload-error',error=str(e))
  if session:bounded(3,session.detach);emit(stage='session-detached')
  emit(stage='session-ended',source_restored=before is not None and source.exists() and source.read_bytes()==before)
if failed:raise SystemExit(1)
