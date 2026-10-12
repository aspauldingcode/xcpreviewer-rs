import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 fixture=e/'fixture';receipt=json.loads((fixture/'receipt.json').read_text());assert receipt['source_sha256']=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8' and receipt['source_sha256']==hashlib.sha256((fixture/'source.swift').read_bytes()).hexdigest() and receipt['module_sha256']==hashlib.sha256((fixture/'view.wasm').read_bytes()).hexdigest() and receipt['generated_sha256']==hashlib.sha256((fixture/'module.rs').read_bytes()).hexdigest();assert len((fixture/'expected.raw').read_bytes())==16384
 d=json.loads((e/'result.json').read_text());assert d['actualCompilerJobs']==0 and d['syntheticRequests']==280 and len(d['results'])==4 and {(r['phase'],r['name']) for r in d['results']}=={(p,n) for p in ['before','after'] for n in ['default','configured']};all_files=set();requests=0
 for r in d['results']:
  n=130 if r['name']=='default' else 10;limit=64 if r['name']=='default' else 4;before=r['phase']=='before';count=n//2 if before else limit;assert r['requests']==r['rawStageCount']==n and r['limit']==limit and len(r['records'])==len(r['failures'])==count;requests+=n
  assert r['history']==(None if before else {'limit':limit,'recordsDropped':1,'failuresDropped':1})
  expected_odd=list(range(1,n+1,2))[-count:];expected_even=list(range(2,n+1,2))[-count:];assert [x['execution']['syntheticJobId'] for x in r['records']]==expected_odd and [x['record']['syntheticJobId'] for x in r['failures']]==expected_even
  for record in r['records']:
   assert record['receipt']==receipt and json.loads(record['execution']['stdout'])==receipt and record['execution']['stderr']=='' and record['execution']['report']=={'drained':True,'remaining_observed':0,'target_code':0,'scope':'Synthetic execution boundary'} and Path(record['stage']).name==record['stage']
  for failure in r['failures']:assert failure=={'error':'Error: Owned history failure '+str(failure['record']['syntheticJobId']),'record':{'syntheticJobId':failure['record']['syntheticJobId'],'scope':'Synthetic execution boundary'}}
  assert [x['id'] for x in r['retainedFailures']]==list(range(2,n+1,2))
  for failure in r['retainedFailures']:
   name=failure['file'];assert Path(name).name==name and name==r['phase']+'-'+r['name']+'-'+str(failure['id'])+'.json' and name not in all_files;all_files.add(name);assert json.loads((e/'retained-failures'/name).read_text())=={'error':'Error: Owned history failure '+str(failure['id']),'record':{'syntheticJobId':failure['id'],'scope':'Synthetic execution boundary'}}
 assert requests==280 and len(all_files)==140 and all_files=={p.name for p in (e/'retained-failures').iterdir()}
 assert d['invalid']==[{'value':x,'rejected':True,'rootCreated':False} for x in [0,257,-1,1.5,True,'4']]
 scope=json.loads((e/'scope.json').read_text());assert scope=={'native_canvas_qualified':False,'actual_compiler_jobs':0,'synthetic_requests':280,'retained_failure_artifacts':140,'entry_bytes_bound_qualified':False,'raw_disk_quota_qualified':False,'history_count_bound_qualified':True,'history_default':64,'history_minimum':1,'history_maximum':256}
 env=json.loads((e/'environment.json').read_text());assert env['actual_compiler_jobs']==0 and env['synthetic_requests']==280 and env['budgets']=={'node_seconds':12,'history_default':64,'history_maximum':256} and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e';assert (e/'control.stderr').read_bytes()==b''
 return {'synthetic_requests':280,'retained_failures':140,'default_history_limit':64,'configured_limit':4,'count_bound_verified':True,'native_compiler_jobs':0,'raw_disk_quota_qualified':False}
