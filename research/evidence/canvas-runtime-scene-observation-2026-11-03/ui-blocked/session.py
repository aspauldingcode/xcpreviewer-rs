"""Bounded native class weak-observation session; UI actions remain operator-controlled."""
from pathlib import Path
import argparse,subprocess,hashlib,fcntl,frida,threading,json,time
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pid',type=int,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--control',type=Path,required=True);a=p.parse_args()
r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);root=Path(__file__).resolve().parents[3]
for name in ['agent.js','session.py','weak.swift','control.c']:(r/name).write_bytes(Path(__file__).with_name(name).read_bytes())
failed=False
ready=threading.Event();acks={};mutex=threading.Lock();session=None;script=None

def emit(**value):
 value['time_ns']=time.monotonic_ns()
 with mutex:
  with (r/'events.jsonl').open('a') as f:f.write(json.dumps(value)+'\n')
def bounded(seconds,call):
 c=frida.Cancellable();t=threading.Timer(seconds,c.cancel);t.start()
 try:
  with c:return call()
 finally:t.cancel()
def message(m,data):
 emit(stage='script',message=m);v=m.get('payload',{})
 if v.get('event')=='hooks-ready':ready.set()
 if v.get('event') in ['snapshot','cleanup-done']:
  label=v['label'];(r/(label+'.json')).write_text(json.dumps(v,indent=2)+'\n')
  if label in acks:acks[label].set()
def command(label,cleanup=False):
 acks[label]=threading.Event();bounded(3,lambda:script.post({'type':'command','payload':{'label':label,'cleanup':cleanup}}))
 if not acks[label].wait(5):raise TimeoutError('main queue acknowledgement: '+label)
with open(root/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  assert subprocess.check_output(['ps','-p',str(a.pid),'-o','comm='],timeout=3).decode().strip()=='/Applications/Xcode.app/Contents/MacOS/Xcode'
  image=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsScenes.framework/Versions/A/PreviewsScenes');assert hashlib.sha256(image.read_bytes()).hexdigest()=='e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09'
  control=subprocess.run([str(a.control.resolve())],capture_output=True,text=True,timeout=5);(r/'control.stdout').write_text(control.stdout);(r/'control.stderr').write_text(control.stderr);assert control.returncode==0
  emit(stage='owned-controls-passed',count=3,library_sha256=hashlib.sha256(a.library.read_bytes()).hexdigest())
  session=bounded(8,lambda:frida.get_local_device().attach(a.pid));code=(r/'agent.js').read_text().replace('__WEAK_LIBRARY__',json.dumps(str(a.library.resolve())));(r/'executed-agent.js').write_text(code);script=session.create_script(code);script.on('message',message);bounded(8,script.load);assert ready.wait(2)
  (r/'ready').touch();emit(stage='capture-ready');end=time.monotonic()+240;done=set()
  while time.monotonic()<end and not (r/'stop').exists():
   for label in ['baseline','unpinned','new-tab','after-close','restored']:
    if (r/('poll-'+label)).exists() and label not in done:command(label);done.add(label)
   time.sleep(.1)
 except Exception as e:failed=True;emit(stage='failure',error=str(e),kind=type(e).__name__)
 finally:
  if script and ready.is_set():
   try:command('cleanup',True)
   except Exception as e:emit(stage='cleanup-unconfirmed',error=str(e))
  if script:
   try:bounded(3,script.unload)
   except Exception as e:emit(stage='unload-error',error=str(e))
  if session:bounded(3,session.detach)
  emit(stage='session-ended-no-target-termination')

if failed:raise SystemExit(1)
