import hashlib,json
from pathlib import Path
CASES=[('ascii-under','x'*1016),('ascii-exact','x'*1017),('ascii-over','x'*1018),('emoji','🙂'*400),('accent','é'*700),('log','Owned failure')]
def excerpt(text):return text.encode()[:1024].decode('utf-8','ignore')
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
 d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==12 and d['actualCompilerJobs']==0 and len(d['rows'])==12;total=0
 for n,row in enumerate(d['rows']):
  phase='before' if n<6 else 'after';name,message=CASES[n%6];original='Error: '+message;size=len(original.encode());assert row['phase']==phase and row['name']==name and row['originalPreserved'] is True and row['originalBytes']==size and row['writes']==1 and row['budget']=={'stageLimit':64,'stagesCreated':1}
  failure={'error':original if phase=='before' else excerpt(original)}
  if phase=='after' and size>1024:failure['error_original_bytes']=size
  if name=='log':
   log='Error: '+'🙂'*400;assert row['logOriginalBytes']==len(log.encode());failure['persistence_error']=log if phase=='before' else excerpt(log)
   if phase=='after':failure['persistence_error_original_bytes']=len(log.encode())
  else:assert row['logOriginalBytes'] is None
  assert row['failure']==failure
  files=['source.swift'] if name=='log' else ['failure.json','source.swift'];assert row['files']==files;stage=row['stage'];assert Path(stage).name==stage and stage.startswith('build-');root=e/(phase+'-'+name);assert {p.name for p in root.iterdir()}=={stage};base=root/stage;assert sorted(p.name for p in base.iterdir())==files and (base/'source.swift').read_bytes()==source;total+=len(source)
  if name!='log':assert json.loads((base/'failure.json').read_text())==failure
 assert total==2424 and json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'diagnostic_excerpt_limit':1024,'execution_record_byte_quota_qualified':False,'per_stage_byte_quota_qualified':False,'source_bytes':2424}
 assert json.loads((e/'environment.json').read_text())=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':8}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'controls':12,'calls':12}
 p=json.loads((e/'prediction.json').read_text());assert p['error_limit_bytes']==1024 and p['code_point_boundary'] is True and p['original_error_preserved'] is True and p['before_oversize_retained'] is True and p['after_oversize_retained'] is False and p['native_jobs']==0 and p['budget_seconds']==8
 return {'failure_controls':12,'retained_source_bytes':2424,'diagnostic_excerpt_limit':1024,'actual_compiler_jobs':0,'record_byte_quota_qualified':False}
