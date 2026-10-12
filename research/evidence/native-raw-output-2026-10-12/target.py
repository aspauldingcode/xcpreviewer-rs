import os,sys,time,json,signal
from pathlib import Path
root=Path(sys.argv[1]);signal.alarm(6);readfd,writefd=os.pipe();child=os.fork()
if child==0:
 signal.alarm(6)
 os.close(readfd)
 def terminate(sig,frame):
  (root/'child.raw').write_bytes(bytes([0,1,2,255,10,42,99,128]));os._exit(42)
 signal.signal(signal.SIGTERM,terminate)
 os.write(writefd,b'ready');os.close(writefd)
 deadline=time.monotonic()+2
 while not (root/'gate').exists() and time.monotonic()<deadline:time.sleep(.001)
 if not (root/'gate').exists():os._exit(44)
 os.setsid()
 while True:time.sleep(.01)
os.close(writefd)
def terminate_parent(sig,frame):
 deadline=time.monotonic()+1
 while True:
  pid,status=os.waitpid(child,os.WNOHANG)
  if pid:
   (root/'child-wait.json').write_text(json.dumps({'pid':pid,'raw_status':status,'exited':os.WIFEXITED(status),'exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None}));os._exit(43)
  if time.monotonic()>deadline:os._exit(45)
  time.sleep(.001)
signal.signal(signal.SIGTERM,terminate_parent)
ack=os.read(readfd,5);os.close(readfd)
assert ack==b'ready'
(root/'ready.json').write_text(json.dumps({'parent_pid':os.getpid(),'child_pid':child,'child_ack':ack.decode(),'parent_group':os.getpgrp()}))
(root/'gate').write_text('go')
while True:time.sleep(.01)
