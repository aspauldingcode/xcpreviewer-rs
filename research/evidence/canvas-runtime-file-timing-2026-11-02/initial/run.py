from pathlib import Path
import frida,fcntl,threading,time,json,hashlib,subprocess
import argparse,sys
parser=argparse.ArgumentParser(description="Observe three real Xcode builds in an explicitly selected owned fixture")
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--workspace',type=Path,required=True)
parser.add_argument('--pid',type=int,required=True)
args=parser.parse_args()
r=args.output.resolve();r.mkdir(exist_ok=False,parents=True)
root=Path('/Users/8amps/xcpreviewer-rs')
source=args.source.resolve();workspace=str(args.workspace.resolve())
assert source.is_relative_to(root/'research/build/preview-workspaces'), 'requires owned fixture'
assert args.workspace.resolve().is_relative_to(root/'research/build/preview-workspaces'), 'requires owned fixture'
assert '"' not in workspace and '\\' not in workspace, 'unsupported AppleScript path'
agent=Path('/private/tmp/canvas-file-timing-runtime-20261102/agent.js').read_text()
(r/'agent.js').write_text(agent)
(r/'run.py').write_bytes(Path(__file__).read_bytes())
before=None;failed=False

for name,digest in [('PreviewsXcode','ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'),('PreviewsIDEAPI','d3e0ad14a4ea159fde12482d92fb7b7d3f86e4df1578fcef76961a294fbe71f0')]:assert hashlib.sha256((Path('/Applications/Xcode.app/Contents/PlugIns')/(name+'.framework/Versions/A')/name).read_bytes()).hexdigest()==digest
ready=threading.Event();early_done=threading.Event();session=None;script=None;phase='setup';edited=False;bad=None;early_error=None

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
 if m.get('type')=='send' and m.get('payload',{}).get('event')=='build-timestamp-written' and phase=='early' and not early_done.is_set():
  global bad,edited,early_error
  try:
   time.sleep(.2)
   assert source.read_bytes()==before,'concurrent edit'
   bad=before+b'\n// native runtime early file modification\n';source.write_bytes(bad);edited=True
   emit(stage='early-file-write',sha256=hashlib.sha256(bad).hexdigest())
  except Exception as e:early_error=str(e);emit(stage='early-file-write-failed',error=str(e))
  finally:early_done.set()

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
with open(root/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  before=source.read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef', 'source identity mismatch'
  (r/'source-backup.swift').write_bytes(before)
  device=bounded('device',3,frida.get_local_device);process=bounded('identity',3,lambda:next(p for p in device.enumerate_processes() if p.pid==args.pid));assert process.name=='Xcode'
  session=bounded('attach',8,lambda:device.attach(process.pid));script=session.create_script(agent);script.on('message',message);bounded('load-hooks',5,script.load);assert ready.wait(1),'hooks not ready'
  phase='baseline';bounded('phase-baseline',2,lambda:script.exports_sync.phase(phase));time.sleep(2)
  phase='early';bounded('phase-early',2,lambda:script.exports_sync.phase(phase));build();assert early_done.wait(2),'early edit missing';assert early_error is None,early_error
  phase='settle';bounded('phase-settle',2,lambda:script.exports_sync.phase(phase));time.sleep(3)
  phase='late';bounded('phase-late',2,lambda:script.exports_sync.phase(phase));assert source.read_bytes()==bad,'concurrent edit';bad=before+b'\n// native runtime late file modification\n';source.write_bytes(bad);emit(stage='late-file-write',sha256=hashlib.sha256(bad).hexdigest());time.sleep(5)
  phase='restore';bounded('phase-restore',2,lambda:script.exports_sync.phase(phase));assert source.read_bytes()==bad,'concurrent edit';source.write_bytes(before);edited=False;emit(stage='source-restored',sha256=hashlib.sha256(before).hexdigest());time.sleep(3)
  emit(status='all-file-actions-complete')
 except Exception as e:failed=True;emit(status='failed',error_type=type(e).__name__,error=str(e))
 finally:
  if edited:
   if source.read_bytes()==bad:source.write_bytes(before);emit(stage='source-restored-finally')
   else:emit(stage='restore-skipped-concurrent-edit')
  if script:
   try:bounded('unload',3,script.unload)
   except Exception as e:emit(stage='unload-error',error=str(e))
  if session:bounded('detach',3,session.detach)
  emit(status='detached-no-target-termination',source_restored=before is not None and source.read_bytes()==before)
if failed:sys.exit(1)
