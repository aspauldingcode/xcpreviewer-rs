from pathlib import Path
import frida,fcntl,threading,time,json,hashlib,subprocess
r=Path(__file__).parent;source=Path('/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/PreviewLab.swift');workspace=str(source.parents[2]/'PreviewLab.xcodeproj');before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
for name,digest in [('PreviewsXcode','ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'),('PreviewsIDEAPI','d3e0ad14a4ea159fde12482d92fb7b7d3f86e4df1578fcef76961a294fbe71f0')]:assert hashlib.sha256((Path('/Applications/Xcode.app/Contents/PlugIns')/(name+'.framework/Versions/A')/name).read_bytes()).hexdigest()==digest
ready=threading.Event();session=None;script=None;phase='setup';edited=False

def emit(**d):
 d.update(time_ns=time.monotonic_ns(),phase=phase)
 with (r/'events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
 print(json.dumps(d),flush=True)
def bounded(stage,seconds,call):
 emit(stage=stage,status='begin',deadline_seconds=seconds);c=frida.Cancellable();timer=threading.Timer(seconds,c.cancel);timer.start()
 try:
  with c:v=call()
  emit(stage=stage,status='complete');return v
 finally:timer.cancel()
def message(m,data):
 emit(stage='script',message=m)
 if m.get('type')=='send' and m.get('payload',{}).get('event')=='hooks-ready':ready.set()
def build():
 code='''tell application id "com.apple.dt.Xcode"
set ws to active workspace document
if path of ws is not "%s" then error "Workspace identity mismatch"
set actionResult to build ws
repeat 100 times
 if completed of actionResult then return {completed of actionResult, status of actionResult}
 delay 0.2
end repeat
return {completed of actionResult, "deadline-observed-pending"}
end tell'''%workspace
 (r/(phase+'.applescript')).write_text(code);emit(stage='build-request',status='begin',workspace=workspace)
 try:p=subprocess.run(['osascript',str(r/(phase+'.applescript'))],capture_output=True,timeout=25);row={'code':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'timeout':False}
 except subprocess.TimeoutExpired as e:row={'code':None,'stdout':(e.stdout or b'').decode(),'stderr':(e.stderr or b'').decode(),'timeout':True}
 (r/(phase+'-result.json')).write_text(json.dumps(row,indent=2)+'\n');emit(stage='build-result',**row);assert row['code']==0 and row['stdout'].startswith('true,'),'build did not complete';time.sleep(.4)
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  device=bounded('device',3,frida.get_local_device);process=bounded('identity',3,lambda:next(p for p in device.enumerate_processes() if p.pid==5841));assert process.name=='Xcode'
  session=bounded('attach',8,lambda:device.attach(process.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded('load-hooks',5,script.load);assert ready.wait(1),'hooks not ready'
  phase='success';build()
  assert source.read_bytes()==before,'concurrent source edit';bad=before+b'\nprivate let buildNotificationFailure: = 1\n';source.write_bytes(bad);edited=True;emit(stage='source-error-introduced',sha256=hashlib.sha256(bad).hexdigest())
  phase='failure';build()
  assert source.read_bytes()==bad,'concurrent source edit';source.write_bytes(before);edited=False;emit(stage='source-restored',sha256=hashlib.sha256(before).hexdigest())
  phase='recovery';build();emit(status='all-build-actions-complete')
 except Exception as e:emit(status='failed',error_type=type(e).__name__,error=str(e))
 finally:
  if edited:
   if source.read_bytes()==bad:source.write_bytes(before);emit(stage='source-restored-finally')
   else:emit(stage='restore-skipped-concurrent-edit')
  if script:
   try:script.unload()
   except Exception as e:emit(stage='unload-error',error=str(e))
  if session:session.detach()
  emit(status='detached-no-target-termination',source_restored=source.read_bytes()==before)
