"""Independent packet, queue/failure accounting and full-byte transport reader."""
import hashlib,importlib.util,json,subprocess,shutil,base64
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    sha=lambda b:hashlib.sha256(b).hexdigest();d=json.loads((folder/'channel/result.json').read_text());actual=d['actual'];packets=actual['packets'];assert [p['id'] for p in packets]==[1,2,3,4,5] and all(p['ok'] is True for p in packets)
    assert actual['completed']=={'accepted':5,'rejected':0,'cancelled':0,'writes':5,'closed':True,'reason':None} and not actual['failures'] and len(actual['builds'])==2
    pins=json.loads((folder/'control/config.json').read_text());modules=[]
    for i,build in enumerate(actual['builds']):
        source=(folder/'consumer-input'/f'{i}-source.swift').read_bytes();config=parse(source.decode());assert (config['width'],config['height'])==[(13,7),(9,5)][i];oracle=expected(config,64);assert oracle==(folder/'consumer-input'/f'{i}-expected.raw').read_bytes()
        packet=packets[[1,3][i]]['result'];allocation=base64.b64decode(packet['allocationBase64'],validate=True);assert allocation==oracle and base64.b64encode(allocation).decode()==packet['allocationBase64']
        receipt=build['receipt'];assert receipt['source_sha256']==sha(source) and receipt['config']==config and receipt['rustc_sha256']==pins['rustcSha'] and receipt['toolchain_sha256']==pins['toolchainPin']
        frame=packet['descriptor'];assert frame=={'revision':i+1,'generation':i+1,'sourceSha256':sha(source),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':64*config['height'],'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
        assert packets[[0,2][i]]['result']['frame']==frame
        report=build['execution']['report'];assert report['drained'] is True and report['target_code']==report['remaining_observed']==0 and report['failure'] is None
        stage=folder/'channel/actual'/build['stage']/'result';module=stage/'view.wasm';assert sha(module.read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
        modules.append({'module':str(module),'expected':str(folder/'consumer-input'/f'{i}-expected.raw'),'height':config['height']})
    assert packets[-1]['result']['frame'] is None and actual['final']['lifecycle']['liveWorkers']==actual['final']['lifecycle']['timers']==0
    predictions={'oversize':(0,1,0,0,'request-bound'),'utf8':(0,1,0,0,'invalid-request'),'extra-key':(0,1,0,0,'invalid-request'),'pipeline':(0,1,0,0,'pipelined-input'),'duplicate-id':(1,1,0,1,'invalid-request'),'close-pending':(2,0,1,1,None),'queue-bound':(3,1,2,1,'queue-bound'),'response-bound':(2,1,0,2,None),'backpressure-deadline':(1,1,0,2,'output-failed')}
    assert [r['name'] for r in d['controls']]==list(predictions)
    for row in d['controls']:
        a,r,c,w,reason=predictions[row['name']];assert row['result']=={'accepted':a,'rejected':r,'cancelled':c,'writes':w,'closed':True,'reason':reason}
        assert all(len((json.dumps(p,ensure_ascii=False)+'\n').encode())<=32768 for p in row['packets'])
        if row['name']=='close-pending':assert [p['id'] for p in row['packets']]==[2] and row['packets'][0]['result']=={'closed':True}
        if row['name']=='queue-bound':assert row['packets']==[{'id':3,'ok':False,'error':'queue-bound'}]
        if row['name']=='response-bound':assert row['packets'][0]=={'id':1,'ok':False,'error':'operation-failed'}
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    r=subprocess.run([shutil.which('node'),str(folder/'reader/replay_preview_channel.js'),str((folder/'runtime/tools/re/reloop/preview_channel.js').resolve())],capture_output=True,timeout=5);assert r.returncode==0,r.stderr.decode();return {'actual_modules':2,'complete_bytes':32768,'fault_controls':9,'fresh_stream_replays':3,'review':'pending'}
