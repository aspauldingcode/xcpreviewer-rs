"""Independent restoration predictions, actual waits and complete allocation oracle."""
import base64,hashlib,json,subprocess,shutil
from pathlib import Path
from jsonschema import Draft202012Validator
from reloop.primarysource import parse,expected

def verify(folder):
 e=Path(folder);sha=lambda b:hashlib.sha256(b).hexdigest();manifest=json.loads((e/'manifest.json').read_text());assert set(manifest['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,row in manifest['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
 assert json.loads((e/'prediction.json').read_text())['parentSeal']=='9cdf028d82cdd2930879a26c5d0d1396bd26a48c3a48603c82439f78c2511b74'
 pro=json.loads((e/'sdk-provenance.json').read_text());lock=json.loads((e/'package-lock.json').read_text());assert pro['version']=='2.3.1' and lock['packages']['node_modules/@modelcontextprotocol/client']['integrity']==pro['integrity']
 assert json.loads((e/'control-wait.json').read_text())=={'code':0,'timeout':False}
 official=json.loads((e/'official/schema.json').read_text());assert sha((e/'official/schema.json').read_bytes())=='268a5f82ba70fd7e4b6dc4aa1e64f116f74b4d0edcb69dc046829c79dd4e97e7';v=lambda name:Draft202012Validator({'$schema':official['$schema'],'$defs':official['$defs'],'$ref':'#/$defs/'+name})
 d=json.loads((e/'process/result.json').read_text());assert d['sdkVersion']=='2.3.1' and d['negotiation']=='explicit legacy' and len(d['records'])==1;row=d['records'][0];assert row['mode']=='restore';root=e/'process/restore'
 assert row['wait']==json.loads((root/'wait.json').read_text())=={'timeout':False,'code':0};assert json.loads((root/'partial.json').read_text())=={'wire':row['wire'],'values':row['values']}
 lifecycle=json.loads((root/'builds/session-lifecycle.json').read_text());assert lifecycle==row['lifecycle'];status=lifecycle['final'];l=status['lifecycle'];assert status['frame'] is None and status['readiness']=={'state':'closed','frameRevision':None,'message':'Preview closed.'};assert l['closed'] is True and l['loopClosed'] is True and not l['building'] and not l['busy'] and l['liveWorkers']==l['timers']==0
 assert lifecycle['channel']=={'received':20,'writes':19,'suppressed':0,'closed':True,'reason':'input-ended'};assert json.loads((root/'stderr.txt').read_text())=={'kind':'closed','channel':lifecycle['channel'],'lifecycle':l}
 received=[r['message'] for r in row['wire'] if r['direction']=='receive'];sent=[r['message'] for r in row['wire'] if r['direction']=='send'];assert len(row['wire'])==39 and len(sent)==20 and [r['id'] for r in received]==list(range(19))
 for p in row['wire']:v('JSONRPCMessage').validate(p['message']);assert len(json.dumps(p['message'],separators=(',',':')).encode())<=32768
 v('InitializeResult').validate(received[0]['result']);assert received[0]['result']['serverInfo']=={'name':'owned-preview-handler','version':'0.2.1'};assert received[0]['result']['protocolVersion']=='2025-11-25';v('ListToolsResult').validate(received[1]['result']);assert row['tools']==received[1]['result']
 assert sent[0]['method']=='initialize' and sent[1]=={'jsonrpc':'2.0','method':'notifications/initialized'}
 values=row['values'];assert [r['name'] for r in values]==['frame','start','frame','poll','frame','poll','poll','frame','poll','frame','poll','poll','frame','poll','frame','close','frame'];assert [r['result'] for r in values]==[r['result'] for r in received[2:]]
 for p in received[2:]:v('CallToolResult').validate(p['result'])
 indices=[1,3,5,6,8,10,11,13,15];statuses={i:json.loads(values[i]['result']['content'][0]['text']) for i in indices}
 for i,state,revision,count in zip(indices,['ready','stale','stale','ready','stale','stale','ready','ready','closed'],[1,1,1,2,2,2,3,3,None],[2,3,3,5,6,6,8,8,8]):
  status=statuses[i];assert status['readiness']['state']==state and status['readiness']['frameRevision']==revision and status['diagnostics']['retainedEvents']==count and status['diagnostics']['droppedEvents']==0
 assert statuses[3]==statuses[5] and statuses[8]==statuses[10] and statuses[11]==statuses[13]
 for i,kind in [(3,'unavailable-source'),(8,'invalid-source')]:assert statuses[i]['diagnostics']['latest']==statuses[i]['diagnostics']['lastFailure']=={'kind':kind}
 for i,kind in [(6,'unavailable-source'),(11,'invalid-source')]:assert statuses[i]['diagnostics']['lastFailure']=={'kind':kind} and statuses[i]['diagnostics']['latest']['kind']=='published'
 frameSchema=row['tools']['tools'][3]['outputSchema'];frames={}
 for i in [0,2,4,7,9,12,14,16]:
  r=values[i]['result'];c=r['structuredContent'];assert not list(Draft202012Validator(frameSchema).iter_errors(c));assert r['content']==[{'type':'text','text':'Frame available.' if c['available'] else 'No frame available.'}];frames[i]=c['frame']
 assert frames[0] is None and frames[16] is None and frames[2]==frames[4] and frames[7]==frames[9] and frames[12]==frames[14]
 for i,fi in [(1,2),(3,4),(5,4),(6,7),(8,9),(10,9),(11,12),(13,14)]:assert statuses[i]['frame']==frames[fi]['descriptor']
 assert len(lifecycle['builds'])==3 and lifecycle['failures']==[]
 cfg=json.loads((e/'consumer-config.json').read_text());assert sha(Path(cfg['rustc']).read_bytes())==cfg['rustcSha'];modules=[];complete=0
 source=(e/'consumer-input/0-source.swift').read_bytes();assert sha(source)=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8';config=parse(source.decode());oracle=expected(config,64);assert oracle==(e/'consumer-input/0-expected.raw').read_bytes()
 for i,build_index in [(2,0),(4,0),(7,1),(9,1),(12,2),(14,2)]:
  raw=base64.b64decode(frames[i]['allocationBase64'],validate=True);assert raw==oracle;complete+=len(raw);receipt=lifecycle['builds'][build_index]['receipt']
  assert frames[i]['descriptor']=={'revision':build_index+1,'generation':[1,3,5][build_index],'sourceSha256':sha(source),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':config['height']*64,'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
 stages=[]
 for build in lifecycle['builds']:
  receipt=build['receipt'];stage=root/'builds'/build['stage']/'result';stages.append(build['stage']);assert json.loads((stage/'receipt.json').read_text())==receipt and sha((stage.parent/'source.swift').read_bytes())==receipt['source_sha256']==sha(source) and sha((stage/'view.wasm').read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
  assert receipt['config']==config and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
  for n,pin in receipt['sources'].items():assert sha((e/'runtime/tools/re/rust/canvas-core/src'/n).read_bytes())==pin
  report=build['execution']['report'];assert report['target_code']==report['remaining_observed']==0 and report['drained'] is True and report['failure'] is None
  modules.append({'module':str(stage/'view.wasm'),'expected':str(e/'consumer-input/0-expected.raw'),'height':receipt['config']['height']})
 assert len(set(stages))==3 and len({b['receipt']['module_sha256'] for b in lifecycle['builds']})==1
 script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
 r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=5);assert r.returncode==0 and not r.stderr;assert complete==98304
 return {'owned_servers':1,'fresh_modules':3,'complete_bytes':complete,'restorations':2,'invalid_states':2,'review':'pending'}
