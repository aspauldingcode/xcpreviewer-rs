import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8';d=json.loads((e/'result.json').read_text());assert d['actualChildSpawns']==0 and len(d['results'])==2 and [r['phase'] for r in d['results']]==['before','after'];total=0
 for row in d['results']:
  before=row['phase']=='before';count=4 if before else 0;error='Error: Observed compiler aborted before spawn' if before else 'Error: Rust build aborted before staging';assert row['cancelledRequests']==4 and row['errors']==[error]*4 and row['preFailureCount']==count and row['preStagedSourceBytes']==count*202 and row['preSpawnCount']==0 and len(row['preStages'])==count and row['positiveError']=='Error: Owned noncancelled spawn intercept' and row['interceptedNoncancelledSpawns']==1 and row['records']==[] and len(row['finalStages'])==count+1 and len(row['failures'])==count+1
  assert row['failures']==[{'error':error}]*count+[{'error':'Error: Owned noncancelled spawn intercept'}]
  assert len(set(row['finalStages']))==count+1 and set(row['preStages'])<=set(row['finalStages'])
  base=e/row['phase'];assert set(p.name for p in base.iterdir())==set(row['finalStages'])
  disk_errors=[]
  for stage in row['finalStages']:
   assert Path(stage).name==stage and stage.startswith('build-');folder=base/stage;assert set(p.name for p in folder.iterdir())=={'source.swift','failure.json'};raw=(folder/'source.swift').read_bytes();assert raw==source;total+=len(raw);failure=json.loads((folder/'failure.json').read_text());disk_errors.append(failure['error']);assert failure=={'error':error if stage in row['preStages'] else row['positiveError']}
  assert sorted(disk_errors)==sorted(x['error'] for x in row['failures'])
 assert total==1212
 scope=json.loads((e/'scope.json').read_text());assert scope=={'native_canvas_qualified':False,'actual_compiler_cancel_qualified':False,'actual_child_spawns':0,'pre_cancelled_requests':8,'intercepted_noncancelled_handoffs':2,'retained_source_bytes':1212,'factory_root_creation_unchanged':True}
 env=json.loads((e/'environment.json').read_text());assert env['actual_child_spawns']==env['native_compiler_jobs']==0 and env['requests']==8 and env['positive_handoffs']==2 and env['budgets']=={'node_seconds':8,'source_bytes':4096} and env['node']['version']=='v24.19.0' and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e';assert (e/'control.stderr').read_bytes()==b''
 return {'pre_cancelled_requests':8,'stages_before':4,'stages_after':0,'retained_source_bytes':total,'actual_compiler_jobs':0,'prestage_cancel_verified':True}
