import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8';d=json.loads((e/'result.json').read_text());assert d['actualCompilerJobs']==0 and len(d['results'])==2 and [r['phase'] for r in d['results']]==['before','after'];total=0
 for r in d['results']:
  before=r['phase']=='before';n=3 if before else 2;assert r['preError']=='Error: Rust build aborted before staging' and r['preBudget']==(None if before else {'stageLimit':2,'stagesCreated':0}) and r['budget']==(None if before else {'stageLimit':2,'stagesCreated':2}) and r['stageCount']==r['syntheticHandoffs']==n and r['records']==[] and r['sentinelPreserved'] is True
  assert r['errors']==['Error: Owned stage handoff 1','Error: Owned stage handoff 2','Error: Owned stage handoff 3' if before else 'Error: Rust build stage budget exhausted'] and r['retryError']==(None if before else 'Error: Rust build stage budget exhausted')
  assert r['history']=={'limit':1,'recordsDropped':0,'failuresDropped':n-1} and r['failures']==[{'error':'Error: Owned stage handoff '+str(n),'record':{'syntheticJobId':n,'scope':'Synthetic execution boundary'}}]
  base=e/r['phase'];assert (base/'unrelated.sentinel').read_bytes()==bytes([0,1,2,255,10,42]) and len(r['files'])==n and {p.name for p in base.iterdir()}=={'unrelated.sentinel'}|{x['stage'] for x in r['files']};ids=[]
  for x in r['files']:
   stage=x['stage'];assert Path(stage).name==stage and stage.startswith('build-');folder=base/stage;assert {p.name for p in folder.iterdir()}=={'source.swift','failure.json'};raw=(folder/'source.swift').read_bytes();assert raw==source;total+=len(raw);failure=json.loads((folder/'failure.json').read_text());assert failure==x['failure'];id=failure['record']['syntheticJobId'];ids.append(id);assert failure=={'error':'Error: Owned stage handoff '+str(id),'record':{'syntheticJobId':id,'scope':'Synthetic execution boundary'}}
  assert sorted(ids)==list(range(1,n+1))
 assert total==1010 and d['invalid']==[{'value':x,'rejected':True,'rootCreated':False} for x in [0,257,-1,1.5,True,'2']]
 scope=json.loads((e/'scope.json').read_text());assert scope=={'native_canvas_qualified':False,'actual_compiler_jobs':0,'per_builder_stage_count_qualified':True,'per_stage_byte_quota_qualified':False,'cross_instance_root_quota_qualified':False,'deleted_artifacts':0,'retained_failed_stages':5,'retained_source_bytes':1010,'sentinel_bytes_compared':12}
 env=json.loads((e/'environment.json').read_text());assert env['actual_compiler_jobs']==0 and env['synthetic_handoffs']==5 and env['budgets']=={'node_seconds':8,'stage_default':64,'stage_maximum':256} and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e';assert (e/'control.stderr').read_bytes()==b''
 return {'stage_count_before':3,'stage_count_after':2,'retained_failed_stages':5,'retained_source_bytes':total,'sentinel_bytes':12,'per_builder_budget_verified':True,'cross_instance_quota_qualified':False,'native_compiler_jobs':0}
