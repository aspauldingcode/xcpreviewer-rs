import os,sys,time,json,pathlib
folder=pathlib.Path(sys.argv[1]);readfd,writefd=os.pipe();child=os.fork()
if child==0:
 os.close(readfd);owner=os.getppid();group=os.getpgrp()
 with (folder/'heartbeat.bin').open('wb',buffering=0) as output:
  for i in range(24):
   output.write(bytes([i]));
   if i==0:os.write(writefd,b'1');os.close(writefd)
   time.sleep(0.05)
 (folder/'child-finished.json').write_text(json.dumps({'pid':os.getpid(),'original_parent':owner,'process_group':group,'bytes':24,'self_terminated':True})+'\n');os._exit(0)
os.close(writefd);assert os.read(readfd,1)==b'1';os.close(readfd)
row={'pid':os.getpid(),'child_pid':child,'process_group':os.getpgrp(),'owns_child':True};(folder/'root.json').write_text(json.dumps(row)+'\n');print(json.dumps(row),flush=True)
