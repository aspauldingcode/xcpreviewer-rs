import sys,time,json,faulthandler,functools
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop import core,graphloop,rea
faulthandler.dump_traceback_later(3,repeat=True)
def wrap(mod,name):
 old=getattr(mod,name)
 @functools.wraps(old)
 def wrapped(*a,**kw):
  t=time.monotonic();print(json.dumps({'event':'start','stage':mod.__name__+'.'+name}),flush=True)
  value=old(*a,**kw)
  print(json.dumps({'event':'finish','stage':mod.__name__+'.'+name,'seconds':time.monotonic()-t}),flush=True)
  return value
 setattr(mod,name,wrapped)
for mod,name in [(rea,'runtime_identity'),(core,'source_files'),(graphloop,'identity'),(graphloop,'configuration'),(graphloop,'overlay'),(graphloop,'build')]:wrap(mod,name)
c=core.Controller();view=graphloop.inspect(c)
print(json.dumps({'event':'result','candidates':view['candidates'],'all_milestones_complete':view['all_milestones_complete']}),flush=True)
