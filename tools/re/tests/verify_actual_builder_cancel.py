import hashlib,json
from pathlib import Path
GOLDENS={'0': '13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461', '2': 'bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62'}
SOURCES=['37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8','fedcf8a6469cface25d9f4c28c3b041b957dca31ee511960827abf86c18e990f','d11ab052939b2b5b4b88e58fb0ee1e210772d2a756083bfd6f9d8f34452818cc']
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 expected={int(i):(e/(i+'-expected.raw')).read_bytes() for i in GOLDENS}
 for i,raw in expected.items():assert len(raw)==16384 and hashlib.sha256(raw).hexdigest()==GOLDENS[str(i)]
 assert expected[0]!=expected[2];assert (e/'baseline.raw').read_bytes()==(e/'retained-at-cancel.raw').read_bytes()==expected[0] and (e/'recovered.raw').read_bytes()==expected[2]
 d=json.loads((e/'result.json').read_text());cfg=json.loads((e/'config.json').read_text());env=json.loads((e/'environment.json').read_text());assert d['qualified'] is True and len(d['records'])==2 and len(d['failures'])==1;trigger=d['trigger'];child=trigger['compiler'];assert trigger['generatedBeforeCancel'] is True and trigger['moduleAbsentBeforeCancel'] is True and child['state']=='L' and child['identity'][2]==cfg['rustc'] and all(type(x) is int and x>=0 for x in child['identity'][:2])
 events=d['events'];assert [(x['kind'],x.get('generation')) for x in events]==[('observed',1),('published',1),('observed',2),('observed',3),('rejected',2),('published',3)] and events[4]['error']=='Error: Observed compiler aborted'
 for event in events:
  if event['kind'] in ['observed','published']:assert event['sourceSha256']==SOURCES[event['generation']-1]
 fail=d['failures'][0];r=fail['record'];report=r['report'];assert fail['error']=='Error: Observed compiler aborted' and r['privateAbortRequested'] is True and r['emergencyClosed'] is False and r['anchorCode'] is None and r['signal']=='SIGKILL' and r['stdout']==r['stderr']=='' and report['drained'] is True and report['target_code']==-15 and report['failure']=='abort' and report['remaining_observed']==0 and report['tracked']>=2 and report['observations']>=1
 assert child['group']==r['pid'] and any(row==child for sample in d['observations'] for row in sample) and any(row['pid']==child['parent'] and row['group']==r['pid'] for sample in d['observations'] for row in sample)
 stages=[]
 for index,record in zip([0,2],d['records']):
  stage=record['stage'];assert Path(stage).name==stage;stages.append(stage);base=e/'builds'/stage;receipt=record['receipt'];disk=json.loads((base/'result/receipt.json').read_text());assert receipt==disk and receipt['source_sha256']==SOURCES[index] and receipt['source_sha256']==hashlib.sha256((base/'source.swift').read_bytes()).hexdigest() and receipt['target']=='wasm32-wasip1' and receipt['cache_hit'] is False and receipt['rustc_sha256']==cfg['rustcSha']==env['rustc_sha256'] and receipt['toolchain_sha256']==cfg['toolchainPin'] and receipt['config']=={'width':13,'height':7,'alphas':[4,2,8] if index==0 else [7,7,1],'reverse':0}
  assert receipt['module_sha256']==hashlib.sha256((base/'result/view.wasm').read_bytes()).hexdigest() and receipt['generated_sha256']==hashlib.sha256((base/'result/module.rs').read_bytes()).hexdigest()
  x=record['execution'];p=x['report'];assert x['anchorCode'] is None and x['signal']=='SIGKILL' and x['emergencyClosed'] is False and x['privateAbortRequested'] is False and p['drained'] is True and p['target_code']==0 and p['failure'] is None and p['remaining_observed']==0 and p['tracked']>=1 and p['observations']>=1 and json.loads(x['stdout'])==receipt
 stage=trigger['stage'];assert Path(stage).name==stage and stage not in stages;base=e/'builds'/stage;assert (base/'result/module.rs').is_file() and not (base/'result/view.wasm').exists() and not (base/'result/receipt.json').exists() and hashlib.sha256((base/'source.swift').read_bytes()).hexdigest()==SOURCES[1];assert json.loads((base/'failure.json').read_text())==fail
 assert len(list((e/'builds').glob('build-*')))==3
 status={'liveWorkers':0,'busy':False,'closed':True,'revision':2,'loopClosed':True,'building':False,'timers':0};assert d['finalStatus']==json.loads((e/'closure.json').read_text())==status
 scope=json.loads((e/'scope.json').read_text());assert scope=={'native_canvas_qualified':False,'arbitrary_process_quiescence_qualified':False,'rustc_child_wait_status_observed':False,'fresh_build_jobs':3,'accepted_fresh_builds':2,'rejected_generation':2,'retained_allocations':3,'controlled_bytes':49152,'padding_bytes':252,'unused_tail_bytes':47808}
 assert env['observer_sha256']==cfg['observer']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5' and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['budgets']=={'node_seconds':30,'owned_build_jobs':3,'job_seconds':5,'supervisor_hard_grace_seconds':5}
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0';assert (e/'control.stderr').read_bytes()==b''
 return {'fresh_build_jobs':3,'accepted_builds':2,'cancelled_cli_wait_code':-15,'retained_bytes':49152,'padding_bytes':252,'unused_tail_bytes':47808,'actual_owned_builder_cancel_qualified':True,'native_canvas_qualified':False,'arbitrary_quiescence_qualified':False}
