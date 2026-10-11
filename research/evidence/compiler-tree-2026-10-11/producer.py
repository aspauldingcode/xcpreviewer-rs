import pathlib,sys,json,time,subprocess,importlib.util,uuid
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/compiler-tree-2026-10-11'
 emitter='''import os,sys,time,json,pathlib
root=pathlib.Path(sys.argv[1]);token=sys.argv[2];parent=os.getpid();child=os.fork()
if child==0:
 (root/'child.json').write_text(json.dumps({'pid':os.getpid(),'parent':parent,'group':os.getpgrp(),'token':token}))
 start=time.monotonic();count=0
 while time.monotonic()-start<1.3:
  count+=1;(root/'heartbeat').write_bytes(count.to_bytes(4,'little'));time.sleep(0.01)
 (root/'child-done.json').write_text(json.dumps({'token':token,'count':count}));os._exit(0)
(root/'parent.json').write_text(json.dumps({'pid':parent,'child':child,'group':os.getpgrp(),'token':token}))
time.sleep(2);os.waitpid(child,0)
'''
 (e/'emitter.py').write_text(emitter);realpopen=subprocess.Popen
 for mode in ['baseline','fixed']:
  root=e/mode;root.mkdir();spec=importlib.util.spec_from_file_location(mode,e/(mode+'-sourcecache.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);owned=[];token=str(uuid.uuid4())
  def observed(*args,**kw):
   p=realpopen(*args,**kw);owned.append(p);return p
  with patch.object(module.subprocess,'Popen',side_effect=observed):
   try:module.run_compiler([sys.executable,str(e/'emitter.py'),str(root),token],timeout=0.4)
   except subprocess.TimeoutExpired as ex:error=type(ex).__name__
   else:raise AssertionError('Timeout absent')
  parent=json.loads((root/'parent.json').read_text());child=json.loads((root/'child.json').read_text());assert parent['pid']==owned[0].pid and child['parent']==parent['pid'] and parent['child']==child['pid'] and parent['token']==child['token']==token
  first=(root/'heartbeat').read_bytes();time.sleep(0.08);second=(root/'heartbeat').read_bytes()
  # Baseline descendant has a predeclared short self-exit; wait for that marker, never kill an unknown PID.
  if mode=='baseline':
   deadline=time.monotonic()+2
   while not (root/'child-done.json').exists() and time.monotonic()<deadline:time.sleep(0.01)
   assert (root/'child-done.json').exists()
  final=(root/'heartbeat').read_bytes();time.sleep(0.08);stable=(root/'heartbeat').read_bytes()
  (root/'wait.json').write_text(json.dumps({'error':error,'code':owned[0].returncode,'reaped':owned[0].poll() is not None,'timeout':True,'start_new_session':mode=='fixed','first_hex':first.hex(),'second_hex':second.hex(),'final_hex':final.hex(),'stable_hex':stable.hex(),'child_done':(root/'child-done.json').exists()},indent=2)+'\n');print(mode,owned[0].returncode,int.from_bytes(first,'little'),int.from_bytes(second,'little'),flush=True)
 (e/'environment.json').write_text(json.dumps({'python':sys.version,'python_executable':sys.executable,'platform':sys.platform,'scope':'Owned Python fork/session groups on macOS; no private runtime or native Canvas evidence'},indent=2)+'\n')
