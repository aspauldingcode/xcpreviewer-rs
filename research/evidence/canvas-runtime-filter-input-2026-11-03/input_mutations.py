"""Recorded input-control mutations; none execute native code."""
from pathlib import Path
import argparse,json,tempfile
from verify_input import verify_input
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
original=[json.loads(x) for x in (a.directory/'events.jsonl').read_text().splitlines()]
def event(rs,phase,name):return next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('event')==name and x['message']['payload'].get('phase')==phase)
def field(phase,name,key,value):return lambda rs:event(rs,phase,name).update({key:value})
cases={'deleted-input-empty':field('removed','filter-input-count','count_register','0x0'),'deleted-type-present':field('removed','filter-optional-type','present',True),'deleted-candidate-nonempty':field('removed','filter-candidate-count','count_register','0x1'),'modified-type-absent':field('modified-control','filter-optional-type','present',False),'modified-candidate-empty':field('modified-control','filter-candidate-count','count_register','0x0'),'modified-thunkable-false':field('modified-control','filter-thunkable-result','value',0),'modified-predicate-true':field('modified-control','filter-predicate-result','value',1),'source-not-restored':lambda rs:rs[-1].update(source_restored=False)}
result={}
for name,mutate in cases.items():
 rows=json.loads(json.dumps(original));mutate(rows)
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);(r/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
  try:verify_input(r)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
