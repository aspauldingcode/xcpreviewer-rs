"""Synthetic recorded-evidence fault controls; no native execution."""
import json,tempfile,argparse
from pathlib import Path
from verify import verify
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
original=[json.loads(x) for x in (a.directory/'events.jsonl').read_text().splitlines()]
def stage(rs,name):return next(x for x in rs if x['stage']==name)
def payload(rs,event):return next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('event')==event and x['message']['payload'].get('phase')=='removed')
cases={'file-not-absent':lambda rs:stage(rs,'source-deleted').update(absent=False),'wrong-filter-caller':lambda rs:payload(rs,'removed-filter-enter').update(caller_offset='0x0'),'missing-filter-return':lambda rs:payload(rs,'removed-filter-return').update(event='excluded-return'),'unexpected-propagation':lambda rs:payload(rs,'removed-filter-return').update(event='workspace-removed-enter'),'native-script-error':lambda rs:rs[0].update(message={'type':'error','description':'synthetic'},stage='script'),'source-not-restored':lambda rs:rs[-1].update(source_restored=False),'failed-cli-build':lambda rs:stage(rs,'cli-build-ended').update(code=1),'project-not-restored':lambda rs:rs[-1].update(project_restored=False)}
result={}
for name,mutate in cases.items():
 rs=json.loads(json.dumps(original));mutate(rs)
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);(r/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rs))
  try:verify(r,True)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
