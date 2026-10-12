import os,sys,time,json,pathlib
folder=pathlib.Path(sys.argv[1]);readfd,writefd=os.pipe();child=os.fork()
if child==0:
 os.close(readfd);parent=os.getppid();os.setsid();group=os.getpgrp()
 with (folder/'heartbeat.bin').open('wb',buffering=0) as out:
  for i in range(32):
   out.write(bytes([i]))
   if i==0:os.write(writefd,b'1');os.close(writefd)
   time.sleep(0.05)
 (folder/'child-finished.json').write_text(json.dumps({'pid':os.getpid(),'original_parent':parent,'group':group,'bytes':32,'self_terminated':True})+'\n');os._exit(0)
os.close(writefd);assert os.read(readfd,1)==b'1';os.close(readfd);row={'pid':os.getpid(),'group':os.getpgrp(),'child_pid':child};(folder/'root.json').write_text(json.dumps(row)+'\n');time.sleep(0.45);print(json.dumps(row),flush=True)
