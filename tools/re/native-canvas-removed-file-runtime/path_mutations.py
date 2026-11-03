"""Synthetic path/member evidence faults; no runtime calls or project changes."""
from pathlib import Path
import argparse,json,tempfile
from verify_input import verify_input
from verify_membership import verify_membership
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
def payload(rs,event,phase='removed'):return next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('event')==event and x['message']['payload'].get('phase')==phase)
cases={'primary-wrong-path':('primary',lambda rs:payload(rs,'filter-optional-type').update(path_kind='other')),'getter-not-main':('primary',lambda rs:payload(rs,'filter-optional-type').update(getter_main=False)),'receiver-guard-failed':('primary',lambda rs:payload(rs,'filter-optional-type').update(getter_receiver_expected_family=False)),'getter-unavailable':('primary',lambda rs:payload(rs,'filter-optional-type').update(getter_read_available=False)),'member-wrong-path':('membership',lambda rs:next(x['message']['payload'] for x in rs if x['stage']=='script' and x['message'].get('payload',{}).get('path_kind')=='auxiliary' and x['message']['payload'].get('phase')=='removed').update(path_kind='primary')),'member-file-not-present':('membership',lambda rs:next(x for x in rs if x['stage']=='project-membership-removed').update(file_present=False)),'missing-scene-return':('membership',lambda rs:payload(rs,'scene-update-return').update(event='excluded-return')),'wrong-scene-caller':('membership',lambda rs:payload(rs,'scene-update-enter').update(caller_offset='0x0'))}
result={}
for name,(profile,mutate) in cases.items():
 rows=[json.loads(x) for x in (a.root/profile/'events.jsonl').read_text().splitlines()];mutate(rows)
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);(r/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
  try:(verify_input if profile=='primary' else verify_membership)(r)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
