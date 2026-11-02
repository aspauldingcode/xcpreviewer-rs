from pathlib import Path
import os,subprocess,signal,time,threading,json,frida,fcntl
r=Path(__file__).parent

def bounded(stage,seconds,call):
 c=frida.Cancellable();timer=threading.Timer(seconds,c.cancel);timer.start()
 try:
  with c:return call()
 finally:timer.cancel()

with open(os.environ['XCPREVIEWER_ROOT']+'/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 device=bounded('device',3,frida.get_local_device)
 for mode in ['policy-log-unfulfilled','policy-log-fulfilled']:
  env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env['XCPREVIEWER_POLICY_GATE']='1'
  proc=subprocess.Popen([str(r/'native'),mode],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  stdout=[];stderr=[];events=[];waiting=threading.Event();ready=threading.Event();session=None;script=None;failed=None
  def readout():
   for line in proc.stdout:
    stdout.append(line)
    try:
     if json.loads(line).get('event')=='policy-ready-for-hooks':waiting.set()
    except ValueError:pass
  def readerr():stderr.append(proc.stderr.read())
  def message(m,data):
   events.append(m)
   if m.get('type')=='send' and m.get('payload',{}).get('event')=='hooks-ready':ready.set()
  threads=[threading.Thread(target=readout,daemon=True),threading.Thread(target=readerr,daemon=True)]
  for t in threads:t.start()
  start=time.monotonic()
  try:
   assert waiting.wait(3),'native policy gate not reached'
   assert json.loads(stdout[0])['pid']==proc.pid
   session=bounded('attach',8,lambda:device.attach(proc.pid));script=session.create_script((r/'agent.js').read_text());script.on('message',message);bounded('load',5,script.load);assert ready.wait(1),'hooks not ready'
   proc.stdin.write(b'\n');proc.stdin.flush();proc.wait(timeout=8)
  except Exception as e:failed={'type':type(e).__name__,'error':str(e)}
  finally:
   if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=3)
   for t in threads:t.join(timeout=2)
   time.sleep(.2)
   if session:
    try:session.detach()
    except frida.InvalidOperationError:pass
   (r/(mode+'.stdout')).write_bytes(b''.join(stdout));(r/(mode+'.stderr')).write_bytes(b''.join(stderr));(r/(mode+'.hooks.json')).write_text(json.dumps(events,indent=2)+'\n')
   result={'code':proc.returncode,'pid':proc.pid,'failed':failed,'elapsed_seconds':time.monotonic()-start,'user_xcode_accessed':False}
   (r/(mode+'.trace-result.json')).write_text(json.dumps(result,indent=2)+'\n');print(mode,result,flush=True)
  assert failed is None and proc.returncode==0,'owned logging control did not complete'
