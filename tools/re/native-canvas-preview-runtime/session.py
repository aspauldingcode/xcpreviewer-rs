"""Bounded native file-edit session; operator records Canvas screenshots per phase."""
from pathlib import Path
import argparse,fcntl,frida,hashlib,json,threading,time,subprocess,os
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--pid',type=int,required=True);p.add_argument('--no-hooks',action='store_true');a=p.parse_args()
root=Path(os.environ.get('XCPREVIEWER_ROOT',str(Path(__file__).resolve().parents[3])));r=a.output.resolve();r.mkdir(exist_ok=False,parents=True)
source=a.source.resolve();assert source.is_relative_to(root/'research/build/preview-workspaces');workspace=str(source.parents[2]/'PreviewLab.xcodeproj');assert '"' not in workspace and '\\' not in workspace
(r/'session.py').write_bytes(Path(__file__).read_bytes());(r/'agent.js').write_bytes(Path(__file__).with_name('agent.js').read_bytes())
ready=threading.Event();session=None;script=None;edited=False;ever_edited=False;before=None;failed=False
mutex=threading.Lock()
def emit(**d):
 d['time_ns']=time.monotonic_ns()
 with mutex:
  with (r/'events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
def bounded(seconds,call):
 c=frida.Cancellable();t=threading.Timer(seconds,c.cancel);t.start()
 try:
  with c:return call()
 finally:t.cancel()
def message(m,data):
 emit(stage='script',message=m)
 if m.get('payload',{}).get('event')=='hooks-ready':ready.set()
with open(root/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  actual=subprocess.check_output(['ps','-p',str(a.pid),'-o','comm='],timeout=3).decode().strip();assert actual=='/Applications/Xcode.app/Contents/MacOS/Xcode'
  query='if application id "com.apple.dt.Xcode" is not running then error "Xcode not running"\ntell application id "com.apple.dt.Xcode" to get path of active workspace document'
  actual=subprocess.check_output(['osascript','-e',query],stderr=subprocess.PIPE,timeout=5).decode().strip();assert actual==workspace,'workspace mismatch'
  for name,digest in [('PreviewsScenes','e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09'),('PreviewsUI','26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab')]:
   image=Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(name+'.framework/Versions/A')/name;assert hashlib.sha256(image.read_bytes()).hexdigest()==digest
  before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  (r/'source-before.swift').write_bytes(before);after=before.replace(b'red: 0, green: 0, blue: 1, opacity: 1.0',b'red: 0, green: 0, blue: 0, opacity: 1.0');assert after!=before
  if not a.no_hooks:
   d=bounded(3,frida.get_local_device);session=bounded(8,lambda:d.attach(a.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded(5,script.load);assert ready.wait(1)
  emit(stage='capture-ready',pid=a.pid,hooks=not a.no_hooks);(r/'ready').touch();end=time.monotonic()+120
  while time.monotonic()<end and not (r/'stop').exists():
   if (r/'edit').exists() and not ever_edited:
    assert source.read_bytes()==before,'concurrent source edit';emit(stage='source-edit-begin');source.write_bytes(after);edited=True;ever_edited=True;emit(stage='source-color-edited',sha256=hashlib.sha256(after).hexdigest());(r/'edited').touch()
   if (r/'restore').exists() and edited:
    assert source.read_bytes()==after,'concurrent source edit';source.write_bytes(before);edited=False;emit(stage='source-color-restored');(r/'restored').touch()
   time.sleep(.1)
 except Exception as e:failed=True;emit(stage='failed',kind=type(e).__name__,error=str(e))
 finally:
  if edited:
   if source.read_bytes()==after:source.write_bytes(before);emit(stage='source-restored-finally')
   else:emit(stage='restore-skipped-concurrent-edit')
  if script:
   try:bounded(3,script.unload)
   except Exception as e:emit(stage='unload-error',error=str(e))
  if session:bounded(3,session.detach)
  emit(stage='session-ended-no-target-termination',source_restored=before is not None and source.read_bytes()==before)
if failed:raise SystemExit(1)
