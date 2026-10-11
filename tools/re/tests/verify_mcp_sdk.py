"""Independent sealed SDK transcript, actual child waits and complete byte reader."""
import base64,hashlib,json,subprocess,shutil
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
 folder=Path(folder);sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((folder/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
 for n,row in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts
  p=folder/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
 provenance=json.loads((folder/'sdk-provenance.json').read_text());lock=json.loads((folder/'package-lock.json').read_text())
 assert provenance['version']=='2.3.1' and provenance['package']=='@modelcontextprotocol/client'
 assert lock['packages']['node_modules/@modelcontextprotocol/client']['version']=='2.3.1'
 assert lock['packages']['node_modules/@modelcontextprotocol/client']['integrity']==provenance['integrity']
 assert provenance['parentSeal']=='700c6bfe00763d9a5f54f450acc70444416755838185922e6c4deda87a71401e'
 assert len(provenance['installedFiles'])==1108
 for n in ['node_modules/@modelcontextprotocol/client/dist/index.mjs','node_modules/@modelcontextprotocol/client/dist/stdio.mjs','node_modules/@modelcontextprotocol/core/package.json']:
  assert provenance['installedFiles'][n]['bytes']>0 and len(provenance['installedFiles'][n]['sha256'])==64
 assert json.loads((folder/'control-wait.json').read_text())=={'code':0,'timeout':False}
 d=json.loads((folder/'process/result.json').read_text());assert d['sdkVersion']=='2.3.1' and d['negotiation']=='explicit legacy'
 assert [r['mode'] for r in d['records']]==['edits','eof'];cfg=json.loads((folder/'consumer-config.json').read_text());modules=[];complete=0
 for row in d['records']:
  root=folder/'process'/row['mode'];assert row['wait']==json.loads((root/'wait.json').read_text())=={'timeout':False,'code':0}
  lifecycle=json.loads((root/'builds/session-lifecycle.json').read_text());assert row['lifecycle']==lifecycle
  status=lifecycle['final']['lifecycle'];assert lifecycle['final']['frame'] is None and status['closed'] is True and status['loopClosed'] is True and not status['building'] and status['liveWorkers']==status['timers']==0
  assert json.loads((root/'stderr.txt').read_text())=={'kind':'closed','channel':lifecycle['channel'],'lifecycle':status}
  sent=[w['message'] for w in row['wire'] if w['direction']=='send'];received=[w['message'] for w in row['wire'] if w['direction']=='receive'];count=13 if row['mode']=='edits' else 4
  assert len(sent)==count+1 and [p['id'] for p in received]==list(range(count))
  assert sent[0]['method']=='initialize' and sent[0]['id']==0 and sent[1]=={'jsonrpc':'2.0','method':'notifications/initialized'}
  assert received[0]['result']=={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'owned-preview-handler','version':'0.1.0'}}
  assert row['server']==received[0]['result']['serverInfo'] and row['capabilities']=={'tools':{}} and row['tools']==received[1]['result']
  assert [x['name'] for x in row['tools']['tools']]==['preview_start','preview_poll','preview_status','preview_frame','preview_close']
  assert [x['result'] for x in row['values']]==[p['result'] for p in received[2:]]
  assert lifecycle['channel']=={'received':count+1,'writes':count,'suppressed':0,'closed':True,'reason':'input-ended'}
  values=row['values'];frames=[json.loads(x['result']['content'][0]['text']) for x in values if x['name']=='frame']
  if row['mode']=='edits':
   assert frames[-1] is None;frames=frames[:-1];assert len(frames)==4 and frames[2]==frames[1]
   failure=json.loads(values[4]['result']['content'][0]['text']);assert failure['diagnostics']['lastFailure']['kind']=='rejected' and failure['frame']==frames[1]['descriptor']
   assert values[-1]=={'name':'closed-start','result':{'content':[{'type':'text','text':'Preview operation failed'}],'isError':True}}
   assert len(lifecycle['failures'])==1
   report=lifecycle['failures'][0]['record']['report'];assert report['target_code']==2 and report['drained'] is True and report['remaining_observed']==0
  else:assert len(frames)==1 and lifecycle['failures']==[]
  builds=lifecycle['builds'];assert len(builds)==(3 if row['mode']=='edits' else 1)
  for j,frame in enumerate(frames):
   i=([0,1,1,2][j] if row['mode']=='edits' else 0);source=(folder/'consumer-input'/f'{i}-source.swift').read_bytes();config=parse(source.decode());oracle=expected(config,64)
   raw=base64.b64decode(frame['allocationBase64'],validate=True);assert raw==oracle==(folder/'consumer-input'/f'{i}-expected.raw').read_bytes();complete+=len(raw)
   build=builds[i];receipt=build['receipt'];assert receipt['source_sha256']==sha(source) and receipt['config']==config and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
   assert frame['descriptor']=={'revision':i+1,'generation':[1,2,4][i],'sourceSha256':sha(source),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':64*config['height'],'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
  for i,build in enumerate(builds):
   stage=root/'builds'/build['stage']/'result';receipt=build['receipt'];assert sha((stage/'view.wasm').read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
   for name,pin in receipt['sources'].items():assert sha((folder/'runtime/tools/re/rust/canvas-core/src'/name).read_bytes())==pin
   report=build['execution']['report'];assert report['target_code']==report['remaining_observed']==0 and report['failure'] is None and report['drained'] is True
   modules.append({'module':str(stage/'view.wasm'),'expected':str(folder/'consumer-input'/f'{i}-expected.raw'),'height':receipt['config']['height']})
 script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
 r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode();assert complete==81920
 assert len(json.loads((folder/'retained-failures.json').read_text()))==3
 return {'sdk_version':'2.3.1','owned_servers':2,'fresh_modules':4,'complete_bytes':complete,'review':'pending'}
