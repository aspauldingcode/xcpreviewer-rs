"""Synthetic faults in captured native gate evidence, not native controls."""
from pathlib import Path
import argparse,json,tempfile
from verify import verify
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
original=[json.loads(x) for x in (a.directory/'events.jsonl').read_text().splitlines()]
def payload(rs,name):return next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('event')==name)
def field(event,key,value):return lambda rs:payload(rs,event).update({key:value})
def swap(rs):
 x=next(i for i,v in enumerate(rs) if v.get('message',{}).get('payload',{}).get('event')=='removed-filter-count-branch');y=next(i for i,v in enumerate(rs) if v.get('message',{}).get('payload',{}).get('event')=='removed-empty-cleanup-block');rs[x],rs[y]=rs[y],rs[x]
 times=sorted(v['time_ns'] for v in rs)
 for i,v in enumerate(rs):v['time_ns']=times[i]
cases={'nonzero-count':field('removed-filter-count-branch','count_register','0x1'),'wrong-count-invocation':field('removed-filter-count-branch','id',999),'missing-empty-block':field('removed-empty-cleanup-block','event','excluded-empty'),'count-probe-not-enabled':field('hooks-ready','filter_count_probe',False),'empty-probe-not-enabled':field('hooks-ready','empty_cleanup_probe',False),'empty-before-count':swap,'source-not-restored':lambda rs:rs[-1].update(source_restored=False),'claimed-scene-propagation':lambda rs:next(x for x in rs if x['stage']=='removed-wait-ended').update(workspace_removed_observed=True)}
result={}
for name,mutate in cases.items():
 rows=json.loads(json.dumps(original));mutate(rows)
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);(r/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
  try:verify(r)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
