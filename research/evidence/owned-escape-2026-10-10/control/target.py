import json,os,pathlib,sys,time
folder=pathlib.Path(sys.argv[1]); code=int(sys.argv[2])
child=os.fork()
if child==0:
 os.setsid()
 (folder/'ready.json').write_text(json.dumps({'child':os.getpid(),'parent':os.getppid(),'group':os.getpgrp()}))
 deadline=time.monotonic()+4
 while not (folder/'release').exists() and time.monotonic()<deadline:time.sleep(.01)
 time.sleep(1.2)
 (folder/'late').write_text('late')
 os._exit(0)
deadline=time.monotonic()+4
while not (folder/'release').exists() and time.monotonic()<deadline:time.sleep(.01)
(folder/'exiting').write_text(str(os.getpid()))
os._exit(code)
