import hashlib,json
from pathlib import Path
MODES=['receipt-json','receipt-size','module-digest','generated-digest','report-drained','report-exit']
SOURCES=['37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8','201ed0fc3d92c2896af028f2c7961712b4a183f55e35f36266eb393d985bd953','d11ab052939b2b5b4b88e58fb0ee1e210772d2a756083bfd6f9d8f34452818cc']
GOLDENS=['13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461','bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62']
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256']
 inp=e/'input';sources=[(inp/(str(n)+'-source.swift')).read_bytes() for n in range(3)];assert [sha(b) for b in sources]==SOURCES;gold={n:(inp/(str(n)+'-expected.raw')).read_bytes() for n in [0,2]};assert [sha(gold[n]) for n in [0,2]]==GOLDENS and all(len(b)==16384 for b in gold.values())
 d=json.loads((e/'result.json').read_text());assert d['syntheticHandoffs']==18 and d['nativeCompilerJobs']==0 and [x['mode'] for x in d['rows']]==MODES;total=0
 for row in d['rows']:
  mode=row['mode'];root=e/mode;assert row['handoffs']==3 and row['oracleCalls']==2 and row['budget']=={'stageLimit':64,'stagesCreated':3}
  assert row['failureSnapshot']=={'liveWorkers':1,'busy':False,'closed':False,'revision':1,'loopClosed':False,'building':False,'timers':0} and row['finalStatus']=={'liveWorkers':0,'busy':False,'closed':True,'revision':2,'loopClosed':True,'building':False,'timers':0}
  events=row['events'];assert [(x['kind'],x.get('generation')) for x in events]==[('observed',1),('published',1),('observed',2),('rejected',2),('observed',3),('published',3)]
  for event in events:
   if event['kind'] in ['observed','published']:assert event['sourceSha256']==SOURCES[event['generation']-1]
  assert len(row['records'])==2 and len(row['failures'])==1;stages=set()
  for n,record in zip([0,2],row['records']):
   stage=record['stage'];assert Path(stage).name==stage;stages.add(stage);base=root/'builds'/stage;assert (base/'source.swift').read_bytes()==sources[n];receipt=record['receipt'];expected=json.loads((inp/str(n)/'receipt.json').read_text());assert receipt==expected==json.loads((base/'result/receipt.json').read_text());assert (base/'result/view.wasm').read_bytes()==(inp/str(n)/'view.wasm').read_bytes() and (base/'result/module.rs').read_bytes()==(inp/str(n)/'module.rs').read_bytes();assert record['execution']['scope']=='Synthetic execution boundary' and record['execution']['report']=={'drained':True,'remaining_observed':0,'target_code':0}
  builds=root/'builds';allstages={p.name for p in builds.iterdir()};assert len(allstages)==3 and len(allstages-stages)==1;bad=builds/(allstages-stages).pop();assert (bad/'source.swift').read_bytes()==sources[1];failure=row['failures'][0];assert json.loads((bad/'failure.json').read_text())==failure;execution=failure['record'];assert execution['scope']=='Synthetic execution boundary' and execution['stderr']==''
  expectedReceipt=json.loads((inp/'0/receipt.json').read_text());expectedReceipt['source_sha256']=SOURCES[1];assert json.loads((bad/'result/receipt.json').read_text())==expectedReceipt
  stdout=execution['stdout'];report=execution['report'];assert report=={'drained':mode!='report-drained','remaining_observed':0,'target_code':42 if mode=='report-exit' else 0}
  assert stdout==('{' if mode=='receipt-json' else 'x'*16385 if mode=='receipt-size' else json.dumps(expectedReceipt,separators=(',',':')))
  module=(inp/'0/view.wasm').read_bytes();generated=(inp/'0/module.rs').read_bytes()
  if mode=='module-digest':module=bytes([module[0]^1])+module[1:]
  if mode=='generated-digest':generated+=b'\n// owned mutation\n'
  assert (bad/'result/view.wasm').read_bytes()==module and (bad/'result/module.rs').read_bytes()==generated
  marker='SyntaxError:' if mode=='receipt-json' else 'Rust receipt size limit' if mode=='receipt-size' else 'Receipt digest identity' if mode in ['module-digest','generated-digest'] else 'assert(execution.report.drained'
  assert marker in failure['error'] and marker in events[3]['error'] and len(failure['error'].encode())<=1024 and len(events[3]['error'].encode())<=512
  for name,n in [('baseline',0),('retained',0),('recovered',2)]:
   raw=(root/(name+'.raw')).read_bytes();assert raw==gold[n];total+=len(raw)
 assert total==294912 and json.loads((e/'scope.json').read_text())=={'native_canvas_qualified':False,'fresh_compiler_jobs':0,'synthetic_handoffs':18,'v8_wasm_sequences':6,'retained_allocations':18,'controlled_bytes':294912,'padding_bytes':1512,'unused_tail_bytes':286848}
 env=json.loads((e/'environment.json').read_text());assert env=={'node_sha256':'768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e','node_version':'v24.19.0','wait_code':0,'timeout':False,'native_compiler_jobs':0,'budget_seconds':25,'input_seal':'634fff5175a8cfd4041085e09caf7d1d7607e0f6a3a38b2d4d3963698a08abeb'}
 assert (e/'control.stderr').read_bytes()==b'' and json.loads((e/'control.stdout').read_text())=={'sequences':6,'calls':18}
 p=json.loads((e/'prediction.json').read_text());assert p['modes']==MODES and p['published_generations']==[1,3] and p['rejected_generation']==2 and p['retained_frame_index']==0 and p['recovered_frame_index']==2 and p['native_compiler_jobs']==0 and p['node_seconds']==25
 return {'sequences':6,'controlled_bytes':total,'padding_bytes':1512,'unused_tail_bytes':286848,'native_compiler_jobs':0,'last_valid_frame_retained':True,'owned_workers_closed':True}
