"""Actual deletion/restoration of guarded owned source; no UI or synthetic event."""
from pathlib import Path
import argparse,json,subprocess,hashlib,threading,time,fcntl,frida,signal,os
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pid',type=int,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--auxiliary',action='store_true');p.add_argument('--count-only',action='store_true');p.add_argument('--modify-control',action='store_true');a=p.parse_args();assert not (a.modify_control and a.auxiliary)
r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);root=Path(__file__).resolve().parents[3];source=a.source.resolve()
for n in ['agent.js','session.py']:(r/n).write_bytes(Path(__file__).with_name(n).read_bytes())
mutex=threading.Lock();ready=threading.Event();removed=threading.Event();acks={};script=None;session=None;before=None;deleted=False;failed=False;project=None;project_before=None;project_expected=None;installed=False;primary=source;modified=False;modified_bytes=None

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
 if v.get('event')=='workspace-removed-enter' and v.get('phase')=='removed':removed.set()
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
  session=bounded(8,lambda:frida.get_local_device().attach(a.pid));code=(r/'agent.js').read_text();code=code.replace('const trackEmpty = true;','const trackEmpty = false;') if a.count_only else code;(r/'executed-agent.js').write_text(code);script=session.create_script(code);script.on('message',message);bounded(8,script.load);assert ready.wait(2)
  if a.auxiliary:
   project=primary.parents[2]/'PreviewLab.xcodeproj/project.pbxproj';project_before=project.read_bytes()
   assert hashlib.sha256(project_before).hexdigest()=='1ee671965dcfb221233970e970130946a1971a0b0d30625601e93440a60bcf45'
   source=primary.with_name('RuntimeRefreshDependency.swift');assert not source.exists()
   (r/'project-before.pbxproj').write_bytes(project_before)
   text=project_before.decode()
   replacements=[('children = (A00000000000000000000006); path = PreviewLab;','children = (A00000000000000000000006,A00000000000000000000030); path = PreviewLab;'),('files = (A0000000000000000000000C);','files = (A0000000000000000000000C,A00000000000000000000031);')]
   for old,new in replacements:assert text.count(old)==1;text=text.replace(old,new)
   anchor='  A00000000000000000000007 = {isa = PBXFileReference;';assert text.count(anchor)==1
   text=text.replace(anchor,'  A00000000000000000000030 = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = RuntimeRefreshDependency.swift; sourceTree = "<group>";};\n  A00000000000000000000031 = {isa = PBXBuildFile; fileRef = A00000000000000000000030;};\n'+anchor)
   project_expected=text.encode();before=b'enum RuntimeRefreshDependency { static let token = 1 }\n'
   phase('install');source.write_bytes(before);installed=True;project.write_bytes(project_expected);emit(stage='auxiliary-installed');time.sleep(3)
   phase('cli-build');q=subprocess.Popen(['xcodebuild','-project',str(project.parent),'-scheme','PreviewLab','-configuration','Debug','-destination','platform=macOS','-derivedDataPath',str(r/'derived'),'CODE_SIGNING_ALLOWED=NO','build'],stdout=(r/'cli-build.stdout').open('wb'),stderr=(r/'cli-build.stderr').open('wb'),start_new_session=True)
   try:code=q.wait(timeout=45)
   except subprocess.TimeoutExpired:os.killpg(q.pid,signal.SIGKILL);q.wait();emit(stage='cli-build-timeout');raise
   emit(stage='cli-build-ended',code=code,log_mentions_dependency=b'RuntimeRefreshDependency.swift' in (r/'cli-build.stdout').read_bytes());assert code==0;time.sleep(3)
  phase('baseline');time.sleep(2);assert source.read_bytes()==before
  if a.modify_control:
   phase('modified-control');modified_bytes=before+b'\n// Native filter input runtime control\n';source.write_bytes(modified_bytes);modified=True;emit(stage='source-modified-control');time.sleep(5)
   phase('restore-control');assert source.read_bytes()==modified_bytes,'Concurrent source modification';source.write_bytes(before);modified=False;emit(stage='source-modified-control-restored');time.sleep(4)
  removed.clear();phase('removed');assert source.read_bytes()==before,'Concurrent source edit before deletion';source.unlink();deleted=True;emit(stage='source-deleted',absent=not source.exists());observed=removed.wait(8);emit(stage='removed-wait-ended',workspace_removed_observed=observed);failed=failed or not observed;time.sleep(1)
  phase('restored');assert not source.exists(),'Concurrent source recreation';source.write_bytes(before);deleted=False;emit(stage='source-restored',sha256=hashlib.sha256(source.read_bytes()).hexdigest());time.sleep(3)
 except Exception as e:failed=True;emit(stage='failure',kind=type(e).__name__,error=str(e))
 finally:
  if modified:
   if source.exists() and source.read_bytes()==modified_bytes:source.write_bytes(before);emit(stage='modified-control-restored-finally')
   else:failed=True;emit(stage='modified-restore-skipped-concurrent-edit')
  if deleted:
   if not source.exists():source.write_bytes(before);emit(stage='source-restored-finally')
   else:emit(stage='restore-skipped-concurrent-recreation')
  if installed:
   if project.read_bytes()==project_expected and source.exists() and source.read_bytes()==before:
    project.write_bytes(project_before);source.unlink();emit(stage='auxiliary-cleaned',project_restored=True,dependency_absent=True)
   else:failed=True;emit(stage='auxiliary-cleanup-skipped-concurrent-edit')
  if script and ready.is_set():
   try:phase('cleanup',True)
   except Exception as e:failed=True;emit(stage='cleanup-unconfirmed',error=str(e))
  if script:
   try:bounded(3,script.unload);emit(stage='script-unloaded')
   except Exception as e:failed=True;emit(stage='unload-error',error=str(e))
  if session:bounded(3,session.detach);emit(stage='session-detached')
  emit(stage='session-ended',source_restored=hashlib.sha256(primary.read_bytes()).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef',project_restored=project is None or project.read_bytes()==project_before,auxiliary_absent=not installed or not source.exists())
if failed:raise SystemExit(1)
