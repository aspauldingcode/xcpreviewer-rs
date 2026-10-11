import os,sys,time,json,pathlib
root=pathlib.Path(sys.argv[1]);token=sys.argv[2];parent=os.getpid();child=os.fork()
if child==0:
 (root/'child.json').write_text(json.dumps({'pid':os.getpid(),'parent':parent,'group':os.getpgrp(),'token':token}))
 start=time.monotonic();count=0
 while time.monotonic()-start<1.3:
  count+=1;(root/'heartbeat').write_bytes(count.to_bytes(4,'little'));time.sleep(0.01)
 (root/'child-done.json').write_text(json.dumps({'token':token,'count':count}));os._exit(0)
(root/'parent.json').write_text(json.dumps({'pid':parent,'child':child,'group':os.getpgrp(),'token':token}))
time.sleep(2);os.waitpid(child,0)
