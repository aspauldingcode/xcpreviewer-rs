import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==d['actualCompilerJobs']==0;rows=d['rows'];assert len(rows)==34;total=0;sentinels=set()
 for n,row in enumerate(rows):
  phase='before' if n<17 else 'after';local=n%17;assert row['phase']==phase
  if local<14:
   value=[0,49,5001,-1,1.5,True,'5000'][local//2];existing=local%2==1
   assert type(row['value'])==type(value) and row['value']==value and row['existing'] is existing and row['rootExists'] is (existing or phase=='before') and row['files']==(['sentinel'] if existing else []) and 'Bounded Rust build deadline required' in row['error']
   if existing:
    p=e/phase/('invalid-'+str(n))/'sentinel';assert p.read_bytes()==bytes([0,1,2,255,10,42]);sentinels.add(str(p.relative_to(e)));total+=6
  else:
   value=[50,5000,None][local-14];assert row['value']==value and row['valid'] is True and row['rootExists'] is True and row['files']==[] and row['budget']=={'stageLimit':64,'stagesCreated':0} and row['history']=={'limit':64,'recordsDropped':0,'failuresDropped':0}
 assert total==84 and {str(p.relative_to(e)) for phase in ['before','after'] for p in (e/phase).rglob('*') if p.is_file()}==sentinels
 assert json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'invalid_deadline_no_new_root_qualified':True,'per_stage_byte_quota_qualified':False,'cross_instance_root_quota_qualified':False,'deleted_artifacts':0,'sentinel_bytes':84}
 env=json.loads((e/'environment.json').read_text());assert env=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':8}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'rows':34,'calls':0}
 pred=json.loads((e/'prediction.json').read_text());assert pred['before_invalid_new_root_created'] is True and pred['after_invalid_new_root_created'] is False and pred['existing_sentinel_unchanged'] is True and pred['valid_boundaries']==[50,5000] and pred['default_deadline']==5000 and pred['native_jobs']==0 and pred['budget']=={'node_seconds':8,'producer_slots':4}
 return {'construction_controls':34,'sentinel_bytes':84,'actual_compiler_jobs':0,'invalid_deadline_no_new_root_verified':True}
