import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 d=json.loads((e/'results.json').read_text());assert set(d)=={'omitted','unrelated','complete'}
 for case in d:
  for phase in ['before','after']:
   result=d[case][phase];reject=phase=='after' and case!='complete'
   assert result=={'accepted':not reject,'error':'Compiler active root missing from observation' if reject else None,'samples':3 if reject else 4,'known':{'10':[1,2,'/owned/root']}}
 scope=json.loads((e/'scope.json').read_text());assert scope['native_processes']==0 and scope['signals']==[] and scope['native_startup_qualified'] is False and scope['native_canvas_qualified'] is False and scope['observer_calls_deadline_guaranteed'] is False
 return {'source_controls':6,'missing_active_root_rejected':True,'native_startup_qualified':False}
