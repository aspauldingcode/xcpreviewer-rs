import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 d=json.loads((e/'results.json').read_text());assert set(d)=={'missing','unrelated','zombie','live','wrong-birth','clean'}
 for case in d:
  for phase in ['before','after']:
   error=None
   if case=='live':error='Observed compiler descendants remain after successful root exit'
   elif case=='wrong-birth':error='Compiler observed lifetime identity changed'
   elif phase=='after' and case in ['missing','unrelated']:error='Compiler descendant retirement was not observed'
   known={'10':[1,2,'/owned/root']}
   if case!='clean':known['11']=[3,4,'/owned/child']
   assert d[case][phase]=={'accepted':error is None,'error':error,'samples':3,'known':known}
 scope=json.loads((e/'scope.json').read_text());assert scope['native_processes']==0 and scope['native_signals']==[] and scope['native_retirement_qualified'] is False and scope['native_startup_qualified'] is False and scope['physical_reclaim_observed'] is False
 return {'source_controls':12,'missing_final_descendant_rejected':True,'native_retirement_qualified':False}
