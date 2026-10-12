import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
 d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==6 and d['actualCompilerJobs']==d['oracleCalls']==0 and len(d['rows'])==6;total=0
 for n,row in enumerate(d['rows']):
  phase='before' if n<3 else 'after';mode=['normal','ENOSPC','EACCES'][n%3];assert row['phase']==phase and row['mode']==mode
  original=phase=='after' or mode=='normal';assert row['originalPreserved'] is original and row['caught']==('Error: Owned build execution failure' if original else 'Error: Owned failure log '+mode)
  assert row['writes']==1 and row['persisted'] is (mode=='normal') and row['budget']=={'stageLimit':64,'stagesCreated':1} and row['records']==[]
  failure={'error':'Error: Owned build execution failure','record':{'scope':'Synthetic execution boundary','id':n}}
  if phase=='after' and mode!='normal':failure['persistence_error']='Error: Owned failure log '+mode
  assert row['failure']==failure;stage=row['stage'];assert Path(stage).name==stage and stage.startswith('build-');root=e/(phase+'-'+mode);assert {p.name for p in root.iterdir()}=={stage};base=root/stage;files=['failure.json','source.swift'] if mode=='normal' else ['source.swift'];assert row['files']==files and sorted(p.name for p in base.iterdir())==files;assert (base/'source.swift').read_bytes()==source;total+=len(source)
  if mode=='normal':assert json.loads((base/'failure.json').read_text())==failure
 assert total==1212
 assert json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'original_failure_preserved_qualified':True,'actual_disk_full_qualified':False,'deleted_artifacts':0,'source_bytes':1212,'failed_log_writes':4}
 assert json.loads((e/'environment.json').read_text())=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':8}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'controls':6,'calls':6,'oracleCalls':0}
 pred=json.loads((e/'prediction.json').read_text());assert pred['before_log_write_masks_original'] is True and pred['after_original_error_preserved'] is True and pred['after_persistence_diagnostic_retained'] is True and pred['controls']==['normal','ENOSPC','EACCES'] and pred['native_jobs']==0 and pred['budget_seconds']==8
 return {'failure_controls':6,'retained_source_bytes':1212,'original_error_preserved':True,'actual_compiler_jobs':0,'actual_disk_full_qualified':False}
