import hashlib,json
from pathlib import Path
MODES=['mutable','cycle','bigint','getter','absent']
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8';d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==10 and d['actualCompilerJobs']==0 and len(d['rows'])==10;total=0
 for n,row in enumerate(d['rows']):
  phase='before' if n<5 else 'after';mode=MODES[n%5];assert row['phase']==phase and row['mode']==mode;original=not(phase=='before' and mode=='getter');error='Error: Owned execution failure '+mode
  assert row['originalPreserved'] is original and row['caught']==(error if original else 'Error: Owned record getter failure') and row['budget']=={'stageLimit':64,'stagesCreated':1} and row['records']==[]
  persisted=phase=='after' or mode in ['mutable','absent'];files=['failure.json','source.swift'] if persisted else ['source.swift'];assert row['files']==files;stage=row['stage'];assert Path(stage).name==stage and stage.startswith('build-');root=e/(phase+'-'+mode);assert {p.name for p in root.iterdir()}=={stage};base=root/stage;assert sorted(p.name for p in base.iterdir())==files and (base/'source.swift').read_bytes()==source;total+=len(source)
  if phase=='before' and mode in ['cycle','bigint']:
   assert row['failures'] is None and row['disk'] is None and ('circular structure' if mode=='cycle' else 'BigInt') in row['readError']
  elif phase=='before' and mode=='getter':assert row['failures']==[] and row['readError'] is None and row['disk'] is None
  else:
   assert row['readError'] is None and len(row['failures'])==1;failure=row['failures'][0];assert failure['error']==error
   if mode=='mutable':assert failure=={'error':error,'record':{'scope':'Owned record','value':2 if phase=='before' else 1}};assert row['disk']=={'error':error,'record':{'scope':'Owned record','value':1}}
   elif mode=='absent':assert failure==row['disk']=={'error':error}
   else:
    assert set(failure)=={'error','record_error'} and len(failure['record_error'].encode())<=1024 and ('circular structure' if mode=='cycle' else 'BigInt' if mode=='bigint' else 'Owned record getter failure') in failure['record_error'] and row['disk']==failure
  if persisted:assert json.loads((base/'failure.json').read_text())==row['disk']
 assert total==2020 and json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'retained_record_snapshot_qualified':True,'record_byte_quota_qualified':False,'source_bytes':2020}
 assert json.loads((e/'environment.json').read_text())=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':8}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'controls':10,'calls':10}
 p=json.loads((e/'prediction.json').read_text());assert p['cases']==MODES and p['after_original_preserved'] is True and p['after_json_readable'] is True and p['after_mutation_stable'] is True and p['native_jobs']==0 and p['budget_seconds']==8
 return {'failure_controls':10,'retained_source_bytes':2020,'snapshot_preserved':True,'actual_compiler_jobs':0,'record_byte_quota_qualified':False}
