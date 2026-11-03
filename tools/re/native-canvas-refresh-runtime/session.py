"""Bounded existing preview probes with acknowledged native-UI/file experiment phases."""
from pathlib import Path
import argparse,fcntl,frida,hashlib,json,subprocess,threading,time
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pid',type=int,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
for n in ['session.py','agent.js']:(out/n).write_bytes(Path(__file__).with_name(n).read_bytes())
source=a.source.resolve();assert source.is_relative_to(root/'research/build/preview-workspaces')
lock=threading.Lock();ready=threading.Event();session=None;script=None;before=None;after=None;edited=False;failed=False
start=time.monotonic_ns()
def emit(**v):
 v['time_ns']=time.monotonic_ns()-start
 with lock:
  with (out/'events.jsonl').open('a') as f:f.write(json.dumps(v)+'\n')
def bounded(seconds,call):
 c=frida.Cancellable();timer=threading.Timer(seconds,c.cancel);timer.start()
 try:
  with c:return call()
 finally:timer.cancel()
def message(m,data):
 emit(stage='script',message=m)
 if m.get('payload',{}).get('event')=='hooks-ready':ready.set()
labels=['idle-start','idle-end','refresh-start','refresh-return','refresh-settled','edit','edit-settled','restore','restore-settled']
with open(root/'research/state/controller.lock','a+') as lease:
 fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  assert subprocess.check_output(['ps','-p',str(a.pid),'-o','comm='],timeout=3).decode().strip()=='/Applications/Xcode.app/Contents/MacOS/Xcode'
  for name,digest in [('PreviewsScenes','e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09'),('PreviewsUI','26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab')]:
   image=Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(name+'.framework/Versions/A')/name;assert hashlib.sha256(image.read_bytes()).hexdigest()==digest
  before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  after=before.replace(b'red: 0, green: 0, blue: 1, opacity: 1.0',b'red: 0, green: 0, blue: 0, opacity: 1.0');assert before!=after
  session=bounded(8,lambda:frida.get_local_device().attach(a.pid));script=session.create_script((out/'agent.js').read_text());script.on('message',message);bounded(5,script.load);assert ready.wait(2)
  emit(stage='capture-ready',pid=a.pid);(out/'ready').touch();deadline=time.monotonic()+150;done=set()
  while time.monotonic()<deadline and not (out/'stop').exists():
   for label in labels:
    if (out/('command-'+label)).exists() and label not in done:
     if label=='edit':
      assert source.read_bytes()==before,'Concurrent source edit';source.write_bytes(after);edited=True
     elif label=='restore':
      assert edited and source.read_bytes()==after,'Concurrent edit or missing edit';source.write_bytes(before);edited=False
     emit(stage='phase',label=label,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest());(out/(label+'.ack')).touch();done.add(label)
   time.sleep(.05)
  if len(done)!=len(labels):raise RuntimeError('Incomplete phase protocol')
 except Exception as exc:failed=True;emit(stage='failure',kind=type(exc).__name__,error=str(exc))
 finally:
  if edited:
   if source.read_bytes()==after:source.write_bytes(before);emit(stage='source-restored-finally')
   else:failed=True;emit(stage='restore-skipped-concurrent-edit')
  if script:
   try:bounded(3,script.unload);emit(stage='script-unloaded')
   except Exception as exc:failed=True;emit(stage='unload-error',error=str(exc))
  if session:
   try:bounded(3,session.detach);emit(stage='session-detached')
   except Exception as exc:failed=True;emit(stage='detach-error',error=str(exc))
  emit(stage='session-ended-no-target-termination',source_restored=before is not None and source.read_bytes()==before)
if failed:raise SystemExit(1)
