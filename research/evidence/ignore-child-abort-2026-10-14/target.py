import os,sys,time,json,signal
from pathlib import Path
root=Path(sys.argv[1]);code=int(sys.argv[2]);assert code==43;policy=sys.argv[3];assert policy in ["running","stopped"];signal.alarm(6);readfd,writefd=os.pipe();child=os.fork()
if child==0:
 signal.alarm(6)
 os.close(readfd)
 def terminate(sig,frame):
  (root/'child.raw').write_bytes(bytes([0,1,2,255,10,42,99,128]));os._exit(42)
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 os.write(writefd,b'ready');os.close(writefd)
 deadline=time.monotonic()+2
 while not (root/'gate').exists() and time.monotonic()<deadline:time.sleep(.001)
 if not (root/'gate').exists():os._exit(44)
 os.setsid()
 while True:
  if policy=='stopped' and (root/'stop').exists():
   (root/'stopped-marker.raw').write_bytes(bytes([0,1,2,255,10,42,99,128]));os.kill(os.getpid(),signal.SIGSTOP)
  time.sleep(.001)
os.close(writefd)
ack=os.read(readfd,5);os.close(readfd)
assert ack==b'ready'
(root/'ready.json').write_text(json.dumps({'parent_pid':os.getpid(),'child_pid':child,'child_ack':ack.decode(),'parent_group':os.getpgrp()}))
(root/'gate').write_text('go')
while True:time.sleep(.001)
