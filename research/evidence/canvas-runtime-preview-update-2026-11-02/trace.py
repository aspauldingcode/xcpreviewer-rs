from pathlib import Path
import frida,threading,json,time
r=Path(__file__).parent;ready=threading.Event();session=None;script=None
def emit(**d):
 d['time_ns']=time.monotonic_ns()
 with (r/'events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
def bounded(stage,seconds,call):
 c=frida.Cancellable();t=threading.Timer(seconds,c.cancel);t.start()
 try:
  with c:return call()
 finally:t.cancel()
def message(m,data):
 emit(stage='script',message=m)
 if m.get('payload',{}).get('event')=='hooks-ready':ready.set()
try:
 d=bounded('device',3,frida.get_local_device);p=next(p for p in d.enumerate_processes() if p.pid==45749);assert p.name=='Xcode'
 session=bounded('attach',8,lambda:d.attach(p.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded('load',5,script.load);assert ready.wait(1);(r/'hooks-ready').touch();emit(stage='capture-ready',pid=p.pid)
 end=time.monotonic()+120
 while time.monotonic()<end and not (r/'trace-stop').exists():time.sleep(.1)
finally:
 if script:
  try:bounded('unload',3,script.unload)
  except Exception as e:emit(stage='unload-error',error=str(e))
 if session:bounded('detach',3,session.detach)
 emit(stage='detached-no-target-termination')
