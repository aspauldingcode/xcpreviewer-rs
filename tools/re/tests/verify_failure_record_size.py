import hashlib,json
from pathlib import Path
CASES=[('ascii-under','x'*(524287-14)),('ascii-exact','x'*(524288-14)),('ascii-over','x'*(524289-14)),('emoji-over','🙂'*131069),('control-escaped','\0'*100000)]
def encoded(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 source=(e/'source.swift').read_bytes();assert len(source)==202 and hashlib.sha256(source).hexdigest()=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8';d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==10 and d['actualCompilerJobs']==0 and len(d['rows'])==10;total=0
 for n,row in enumerate(d['rows']):
  phase='before' if n<5 else 'after';name,payload=CASES[n%5];record={'payload':payload};size=len(encoded(record));assert row['phase']==phase and row['name']==name and row['serializedBytes']==size and row['originalPreserved'] is True and row['originalRecordStillPresent'] is True and row['budget']=={'stageLimit':64,'stagesCreated':1}
  failure={'error':'Error: Owned record size '+name}
  if phase=='after' and size>524288:failure.update(record_original_bytes=size,record_error='Error: Failure record size limit')
  else:failure['record']=record
  assert row['failure']==failure;stage=row['stage'];assert Path(stage).name==stage and stage.startswith('build-');root=e/(phase+'-'+name);assert {p.name for p in root.iterdir()}=={stage};base=root/stage;assert sorted(p.name for p in base.iterdir())==['failure.json','source.swift'] and (base/'source.swift').read_bytes()==source;raw=(base/'failure.json').read_bytes();assert raw==encoded(failure) and row['diskBytes']==len(raw);total+=len(source)
 assert total==2020 and json.loads((e/'scope.json').read_text())=={'actual_compiler_jobs':0,'native_canvas_qualified':False,'retained_failure_record_limit':524288,'initial_serialization_memory_qualified':False,'total_heap_disk_quota_qualified':False,'source_bytes':2020}
 assert json.loads((e/'environment.json').read_text())=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'actual_compiler_jobs':0,'budget_seconds':12}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'controls':10,'calls':10}
 p=json.loads((e/'prediction.json').read_text());assert p['limit_serialized_utf8_bytes']==524288 and p['cases']==[name for name,_ in CASES] and p['oversize_record_omitted'] is True and p['original_error_preserved'] is True and p['native_jobs']==0 and p['budget_seconds']==12
 return {'failure_controls':10,'retained_source_bytes':2020,'record_field_limit':524288,'actual_compiler_jobs':0,'initial_heap_quota_qualified':False}
