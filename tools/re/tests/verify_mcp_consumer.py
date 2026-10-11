"""Independent consumer predictions, actual waits and complete allocation oracle."""
import base64,hashlib,json,subprocess,shutil
from pathlib import Path
from jsonschema import Draft202012Validator
from reloop.primarysource import parse,expected

def verify(folder):
 e=Path(folder);sha=lambda b:hashlib.sha256(b).hexdigest();manifest=json.loads((e/'manifest.json').read_text());assert set(manifest['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,row in manifest['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
 assert json.loads((e/'prediction.json').read_text())['parentSeal']=='79e1fd30e48ce7473dec5fc3b14c2a88ce3fba119610d372f7629d7de1efbef2'
 pro=json.loads((e/'sdk-provenance.json').read_text());lock=json.loads((e/'package-lock.json').read_text());assert pro['version']=='2.3.1' and lock['packages']['node_modules/@modelcontextprotocol/client']['integrity']==pro['integrity']
 assert json.loads((e/'control-wait.json').read_text())=={'code':0,'timeout':False}
 control=json.loads((e/'consumer-controls.json').read_text());assert control['detached'] is True and control['concurrentRejected'] is True
 assert [r['kind'] for r in control['outcomes']]==['rollback','generation','identity','race-limit','availability','hash','readiness','tool-error']
 assert [r['calls'] for r in control['outcomes']]==[3,3,3,6,6,2,1,1] and all(r['rejected'] is True and r['retainedRevision']==2 for r in control['outcomes'])
 for _ in range(2):
  r=subprocess.run([shutil.which('node'),str(e/'control/preview_consumer_control.js'),str(e/'runtime/tools/re/reloop/preview_consumer.js'),str(e/'process/result.json')],capture_output=True,timeout=3);assert r.returncode==0 and not r.stderr and json.loads(r.stdout)==control
 failure=json.loads((e/'retained-failure.json').read_text());assert failure['firstManifestSha256']=='334fcadb5d5a4bd0a89a5dcd2fc1d140ae0b4edaab47c597c58511da255e10f7' and failure['initialStatus']['frame']['width']==1
 deadline=json.loads((e/'retained-deadline.json').read_text());assert deadline['manifestSha256']=='1dd2d0f06d1ca2c9be71899dac531dce66fd9faf81905ee0ee55c1113ea4b751' and deadline['controlWait']=={'code':1,'timeout':False} and deadline['wait']=={'code':0,'timeout':False} and deadline['channel']['reason']=='channel-deadline' and deadline['final']['lifecycle']['liveWorkers']==deadline['final']['lifecycle']['timers']==0
 official=json.loads((e/'official/schema.json').read_text());assert sha((e/'official/schema.json').read_bytes())=='268a5f82ba70fd7e4b6dc4aa1e64f116f74b4d0edcb69dc046829c79dd4e97e7';v=lambda name:Draft202012Validator({'$schema':official['$schema'],'$defs':official['$defs'],'$ref':'#/$defs/'+name})
 d=json.loads((e/'process/result.json').read_text());assert d['sdkVersion']=='2.3.1' and d['negotiation']=='explicit legacy' and len(d['records'])==1;row=d['records'][0];assert row['mode']=='consumer';root=e/'process/consumer'
 assert row['wait']==json.loads((root/'wait.json').read_text())=={'timeout':False,'code':0};assert json.loads((root/'partial.json').read_text())=={'wire':row['wire'],'values':row['values']}
 lifecycle=json.loads((root/'builds/session-lifecycle.json').read_text());assert lifecycle==row['lifecycle'];status=lifecycle['final'];l=status['lifecycle'];assert status['frame'] is None and status['readiness']=={'state':'closed','frameRevision':None,'message':'Preview closed.'};assert l['closed'] is True and l['loopClosed'] is True and not l['building'] and not l['busy'] and l['liveWorkers']==l['timers']==0
 assert lifecycle['channel']=={'received':28,'writes':27,'suppressed':0,'closed':True,'reason':'input-ended'};assert json.loads((root/'stderr.txt').read_text())=={'kind':'closed','channel':lifecycle['channel'],'lifecycle':l}
 received=[r['message'] for r in row['wire'] if r['direction']=='receive'];sent=[r['message'] for r in row['wire'] if r['direction']=='send'];assert len(row['wire'])==55 and len(sent)==28 and [r['id'] for r in received]==list(range(27))
 for p in row['wire']:v('JSONRPCMessage').validate(p['message']);assert len(json.dumps(p['message'],separators=(',',':')).encode())<=32768
 v('InitializeResult').validate(received[0]['result']);assert received[0]['result']['serverInfo']=={'name':'owned-preview-handler','version':'0.2.2'};assert received[0]['result']['protocolVersion']=='2025-11-25';v('ListToolsResult').validate(received[1]['result']);assert row['tools']==received[1]['result']
 assert sent[0]['method']=='initialize' and sent[1]=={'jsonrpc':'2.0','method':'notifications/initialized'}
 values=row['values'];assert [r['name'] for r in values]==['status','frame','status','start','status','frame','status','status','frame','status','status','refresh','frame','status','status','frame','status','refresh','status','frame','status','close','status','frame','status'];assert [r['result'] for r in values]==[r['result'] for r in received[2:]]
 for p in received[2:]:v('CallToolResult').validate(p['result'])
 frameSchema=row['tools']['tools'][3]['outputSchema'];frames={};statuses={}
 for i,r in enumerate(values):
  if r['name']=='frame':
   c=r['result']['structuredContent'];assert not list(Draft202012Validator(frameSchema).iter_errors(c));frames[i]=c['frame']
  else:statuses[i]=json.loads(r['result']['content'][0]['text'])
 assert statuses[4]==statuses[6]==statuses[7]==statuses[9] and statuses[10]['frame']['revision']==1 and statuses[13]['frame']['revision']==2
 assert statuses[14]==statuses[16] and frames[12]==frames[15]==frames[19] and statuses[18]==statuses[20] and statuses[20]['readiness']['state']=='stale'
 assert frames[1] is None and frames[23] is None and len(lifecycle['builds'])==2 and len(lifecycle['failures'])==1
 report=lifecycle['failures'][0]['record']['report'];assert report['target_code']==2 and report['remaining_observed']==0 and report['drained'] is True and report['failure'] is None
 samples=row['samples'];assert len(samples)==6
 for sample,si,fi in zip(samples,[2,6,9,16,20,24],[1,5,8,15,19,23]):assert sample=={'status':statuses[si],'frame':frames[fi]}
 assert [r['status']['readiness']['state'] for r in samples]==['waiting','ready','ready','ready','stale','closed']
 assert [r['status']['readiness']['frameRevision'] for r in samples]==[None,1,1,2,2,None]
 cfg=json.loads((e/'consumer-config.json').read_text());assert sha(Path(cfg['rustc']).read_bytes())==cfg['rustcSha'];modules=[];complete=0
 for i,build_index in [(5,0),(8,0),(12,1),(15,1),(19,1)]:
  source=(e/'consumer-input'/f'{build_index}-source.swift').read_bytes();config=parse(source.decode());oracle=expected(config,64);assert oracle==(e/'consumer-input'/f'{build_index}-expected.raw').read_bytes();raw=base64.b64decode(frames[i]['allocationBase64'],validate=True);assert raw==oracle;complete+=len(raw);receipt=lifecycle['builds'][build_index]['receipt']
  assert frames[i]['descriptor']=={'revision':build_index+1,'generation':build_index+1,'sourceSha256':sha(source),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':config['height']*64,'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
 for sample in samples:
  f=sample['frame']
  if f:raw=base64.b64decode(f['allocationBase64'],validate=True);config=parse((e/'consumer-input'/f"{f['descriptor']['revision']-1}-source.swift").read_text());assert raw==expected(config,64);complete+=len(raw)
 stages=[]
 for index,build in enumerate(lifecycle['builds']):
  source=(e/'consumer-input'/f'{index}-source.swift').read_bytes();config=parse(source.decode())
  receipt=build['receipt'];stage=root/'builds'/build['stage']/'result';stages.append(build['stage']);assert json.loads((stage/'receipt.json').read_text())==receipt and sha((stage.parent/'source.swift').read_bytes())==receipt['source_sha256']==sha(source) and sha((stage/'view.wasm').read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
  assert receipt['config']==config and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
  for n,pin in receipt['sources'].items():assert sha((e/'runtime/tools/re/rust/canvas-core/src'/n).read_bytes())==pin
  report=build['execution']['report'];assert report['target_code']==report['remaining_observed']==0 and report['drained'] is True and report['failure'] is None
  modules.append({'module':str(stage/'view.wasm'),'expected':str(e/'consumer-input'/f'{index}-expected.raw'),'height':receipt['config']['height']})
 assert len(set(stages))==2 and len({b['receipt']['module_sha256'] for b in lifecycle['builds']})==2
 script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
 r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=5);assert r.returncode==0 and not r.stderr;assert complete==147456
 return {'owned_servers':1,'fresh_modules':2,'complete_bytes':complete,'bounded_race_retries':1,'consumer_guards':8,'review':'pending'}
