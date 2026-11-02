import frida,threading,time,json,fcntl,hashlib
from pathlib import Path
r=Path(__file__).parent
p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode');assert hashlib.sha256(p.read_bytes()).hexdigest()=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'
def emit(d):
 d['time_ns']=time.monotonic_ns()
 with (r/'xcode-trace.jsonl').open('a') as o:o.write(json.dumps(d)+'\n')
 print(json.dumps(d),flush=True)
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);session=None
 try:
  c=frida.Cancellable();timer=threading.Timer(4,c.cancel);timer.start()
  try:
   with c:session=frida.get_local_device().attach(5841)
  finally:timer.cancel()
  script=session.create_script('''const m=Process.getModuleByName("PreviewsXcode");send({event:"identity",path:m.path,base:m.base.toString()});for (const [name,offset] of [["build-start-listener",0x16ed0c],["build-stop-listener",0x16ef1c],["workspace-event-handler",0x248ef0]]) {Interceptor.attach(m.base.add(offset),{onEnter(args){send({event:name,thread:Process.getCurrentThreadId()});}});}send({event:"hooks-ready"});''')
  script.on('message',lambda m,data:emit({'message':m}));script.load();emit({'status':'attached','pid':5841});r.joinpath('trace-ready').touch();end=time.monotonic()+120
  while time.monotonic()<end and not (r/'trace-stop').exists():time.sleep(.2)
  script.unload()
 except Exception as e:emit({'status':'attach-or-hook-failed','error_type':type(e).__name__,'error':str(e)})
 finally:
  if session:session.detach()
  emit({'status':'detached-or-not-attached'})
