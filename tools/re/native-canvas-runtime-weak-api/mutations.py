"""Synthetic corruption of captured evidence; none are native runtime controls."""
from pathlib import Path
import argparse,json,tempfile,shutil
from verify import verify
p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
rows=[json.loads(x) for x in (a.run/'events.jsonl').read_text().splitlines()]
def change(event,key,value):
 def f(rs):
  v=next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('event')==event);v[key]=value
 return f
cases={
 'wrong-runtime':change('hooks-ready','runtime_uuid','0'*32),
 'helper-image-loaded':change('hooks-ready','helper_module_loaded',True),
 'non-main-observation':change('editor-scene-observed','main',False),
 'class-guard-false':change('editor-scene-observed','expected_class',False),
 'weak-load-nil':change('editor-scene-observed','weak_alive_at_load',False),
 'unpaired-return':change('method-return','call_id',9999),
 'slot-not-destroyed':change('cleanup-done','weak_slots_destroyed',0),
 'source-not-restored':lambda rs:rs[-1].update(source_restored=False)}
result={}
for name,mutate in cases.items():
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);shutil.copy2(a.run/'control.stdout',r/'control.stdout');copy=json.loads(json.dumps(rows));mutate(copy)
  (r/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in copy))
  try:verify(r)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'kind':'synthetic recorded-evidence faults','results':result},indent=2))
