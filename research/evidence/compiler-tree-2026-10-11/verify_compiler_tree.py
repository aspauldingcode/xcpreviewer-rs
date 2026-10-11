import hashlib,json,uuid
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 pids=[];total=0
 for mode in ['baseline','fixed']:
  root=e/mode;fixed=mode=='fixed';parent=json.loads((root/'parent.json').read_text());child=json.loads((root/'child.json').read_text());wait=json.loads((root/'wait.json').read_text());assert parent['pid']==child['parent'] and parent['child']==child['pid'] and parent['pid']!=child['pid'] and parent['token']==child['token'];uuid.UUID(parent['token']);pids.extend([parent['pid'],child['pid']])
  assert parent['group']==child['group'] and (parent['group']==parent['pid']) is fixed
  assert wait['error']=='TimeoutExpired' and wait['code']==-9 and wait['reaped'] is True and wait['timeout'] is True and wait['start_new_session'] is fixed
  values=[]
  for name in ['first_hex','second_hex','final_hex','stable_hex']:
   raw=bytes.fromhex(wait[name]);assert len(raw)==4;total+=len(raw);values.append(int.from_bytes(raw,'little'))
  first,second,final,stable=values;assert first>0 and final==stable and (first==second if fixed else first<second<=final) and (root/'heartbeat').read_bytes()==bytes.fromhex(wait['stable_hex'])
  assert wait['child_done'] is (not fixed) and (root/'child-done.json').exists() is (not fixed)
  if not fixed:
   done=json.loads((root/'child-done.json').read_text());assert done['token']==parent['token'] and done['count']==final
 assert len(set(pids))==4 and total==32
 return {'producer_processes':4,'heartbeat_bytes':total,'fixed_output_quiescent':True,'descendant_reap_verified':False}
