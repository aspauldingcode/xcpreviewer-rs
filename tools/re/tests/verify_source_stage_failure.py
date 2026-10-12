import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
 d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==2 and d['actualCompilerJobs']==0 and len(d['rows'])==8;total=0
 for n,row in enumerate(d['rows']):
  phase='before' if n<4 else 'after';mode=['ENOSPC','EACCES','source-and-log','execution'][n%4];assert row['phase']==phase and row['mode']==mode
  error='Error: Owned '+('execution' if mode=='execution' else 'source')+' failure '+mode;assert row['originalPreserved'] is True and row['caught']==error and row['sourceWrites']==1 and row['handoffs']==(1 if mode=='execution' else 0)
  retained=phase=='after' or mode=='execution';assert row['logWrites']==(1 if retained else 0) and row['budget']=={'stageLimit':64,'stagesCreated':1} and row['records']==[]
  failure={'error':error}
  if mode=='source-and-log':failure['persistence_error']='Error: Owned log failure ENOSPC'
  assert row['failures']==([failure] if retained else [])
  files=(['failure.json'] if retained and mode!='source-and-log' else [])+(['source.swift'] if mode=='execution' else []);assert row['files']==files;stage=row['stage'];assert Path(stage).name==stage and stage.startswith('build-');root=e/(phase+'-'+mode);expected={stage+'/'+name for name in files};assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==expected
  base=root/stage
  if mode=='execution':assert (base/'source.swift').read_bytes()==source;total+=len(source)
  if 'failure.json' in files:assert json.loads((base/'failure.json').read_text())==failure
 assert total==404
 assert json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'source_write_failure_retained':True,'actual_disk_full_qualified':False,'deleted_artifacts':0,'source_bytes':404}
 assert json.loads((e/'environment.json').read_text())=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':8}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'controls':8,'calls':2}
 p=json.loads((e/'prediction.json').read_text());assert p['before_source_failure_retained'] is False and p['after_source_failure_retained'] is True and p['original_error_preserved'] is True and p['failed_stage_charged'] is True and p['controls']==['ENOSPC','EACCES','source-and-log','execution'] and p['native_jobs']==0 and p['budget_seconds']==8
 return {'failure_controls':8,'retained_source_bytes':404,'source_write_failure_retained':True,'actual_compiler_jobs':0,'actual_disk_full_qualified':False}
