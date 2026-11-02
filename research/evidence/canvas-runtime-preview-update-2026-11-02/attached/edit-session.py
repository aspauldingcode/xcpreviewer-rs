from pathlib import Path
import frida,threading,json,time,fcntl,hashlib
r=Path(__file__).parent;ready=threading.Event();session=None;script=None
def emit(**d):
 d['time_ns']=time.monotonic_ns()
 with (r/'edit-events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
def bounded(stage,seconds,call):
 c=frida.Cancellable();t=threading.Timer(seconds,c.cancel);t.start()
 try:
  with c:return call()
 finally:t.cancel()
def message(m,data):
 emit(stage='script',message=m)
 if m.get('payload',{}).get('event')=='hooks-ready':ready.set()
source=Path('/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/PreviewLab.swift')
lock=open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef';after=before.replace(b'red: 0, green: 0, blue: 1, opacity: 1.0',b'red: 0, green: 0, blue: 0, opacity: 1.0');assert after!=before
(r/'source-before.swift').write_bytes(before);edited=False
try:
 d=bounded('device',3,frida.get_local_device);p=next(p for p in d.enumerate_processes() if p.pid==45749);assert p.name=='Xcode'
 session=bounded('attach',8,lambda:d.attach(p.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded('load',5,script.load);assert ready.wait(1);(r/'edit-ready').touch();emit(stage='capture-ready',pid=p.pid)
 end=time.monotonic()+120
 while time.monotonic()<end and not (r/'edit-stop').exists():
  if (r/'edit-request').exists() and not edited:
   assert source.read_bytes()==before,'concurrent source edit';source.write_bytes(after);edited=True;emit(stage='source-color-edited',sha256=hashlib.sha256(after).hexdigest());(r/'edit-written').touch()
  if (r/'restore-request').exists() and edited:
   assert source.read_bytes()==after,'concurrent source edit';source.write_bytes(before);edited=False;emit(stage='source-color-restored');(r/'restored').touch();break
  time.sleep(.1)
finally:
 if edited:
  if source.read_bytes()==after:source.write_bytes(before);emit(stage='source-restored-finally')
  else:emit(stage='restore-skipped-concurrent-edit')
 if script:
  try:bounded('unload',3,script.unload)
  except Exception as e:emit(stage='unload-error',error=str(e))
 if session:bounded('detach',3,session.detach)
 emit(stage='detached-no-target-termination',source_restored=source.read_bytes()==before);lock.close()
