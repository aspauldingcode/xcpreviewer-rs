import sys,time,json,pathlib
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop import core
from reloop.graphloop import inspect
class ProfileController(core.Controller):
 def verify(self,rid,anchor=None):
  m=core.load(self.runs/rid/'manifest.json',{})
  row={'event':'verify_start','run_id':rid,'declared_files':len(m.get('artifacts',[])),'declared_bytes':sum(a['bytes'] for a in m.get('artifacts',[]))}
  print(json.dumps(row),flush=True);t=time.monotonic()
  result=super().verify(rid,anchor)
  print(json.dumps({'event':'verify_finish','run_id':rid,'seconds':time.monotonic()-t,'valid':result['valid'],'external_anchor_matches':result['external_anchor_matches']}),flush=True)
  return result
with ProfileController().lock():
 t=time.monotonic();result=inspect(ProfileController())
 print(json.dumps({'event':'graph_result','seconds':time.monotonic()-t,'all_milestones_complete':result['all_milestones_complete'],'execution_started':result['execution_started'],'candidates':result['candidates'],'blocked_tasks':result['blocked_tasks']}),flush=True)
