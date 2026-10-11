"""Independent owned process exit, packet identities, oracle and allocation reader."""
import hashlib,importlib.util,json,subprocess,shutil,base64,sys
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    sha=lambda b:hashlib.sha256(b).hexdigest();d=json.loads((folder/'process/result.json').read_text());assert [r['mode'] for r in d['records']]==['edits','eof'];edits,eof=d['records'];cfg=json.loads((folder/'consumer-config.json').read_text());modules=[]
    for row in d['records']:
        assert row['code']==0;final=row['lifecycle']['final'];status=final['lifecycle'];assert final['frame'] is None and status['closed'] is True and status['loopClosed'] is True and status['building'] is False and status['liveWorkers']==status['timers']==0
        summary=json.loads((folder/'process'/row['mode']/'stderr.txt').read_text());assert summary=={'kind':'closed','channel':row['lifecycle']['channel'],'lifecycle':status}
    packets=edits['packets'];assert [p['id'] for p in packets]==list(range(1,10)) and all(p['ok'] is True for p in packets)
    assert edits['lifecycle']['channel']=={'accepted':9,'rejected':0,'cancelled':0,'writes':9,'closed':True,'reason':None};assert len(edits['lifecycle']['builds'])==3 and len(edits['lifecycle']['failures'])==1
    for i,build in enumerate(edits['lifecycle']['builds']):
        source=(folder/'consumer-input'/f'{i}-source.swift').read_bytes();config=parse(source.decode());assert (config['width'],config['height'])==[(13,7),(11,6),(13,7)][i];oracle=expected(config,64)
        packet=packets[[1,3,7][i]]['result'];raw=base64.b64decode(packet['allocationBase64'],validate=True);assert raw==oracle==(folder/'consumer-input'/f'{i}-expected.raw').read_bytes()
        receipt=build['receipt'];assert receipt['source_sha256']==sha(source) and receipt['config']==config and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
        descriptor=packet['descriptor'];assert descriptor=={'revision':i+1,'generation':[1,2,4][i],'sourceSha256':sha(source),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':64*config['height'],'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
        stage=folder/'process/edits/builds'/build['stage']/'result';module=stage/'view.wasm';assert sha(module.read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
        report=build['execution']['report'];assert report['target_code']==report['remaining_observed']==0 and report['drained'] is True and report['failure'] is None
        # Fresh binary oracle process: stdout extent and exact model bytes.
        r=subprocess.run([sys.executable,str(folder/'runtime/tools/re/primary_oracle_cli.py')],input=source,capture_output=True,timeout=3);assert r.returncode==0 and r.stdout==oracle and not r.stderr
        modules.append({'module':str(module),'expected':str(folder/'consumer-input'/f'{i}-expected.raw'),'height':config['height']})
    assert packets[4]['result']['frame']==packets[3]['result']['descriptor'] and packets[4]['result']['diagnostics']['lastFailure']['kind']=='rejected'
    assert packets[5]['result']==packets[3]['result'] and base64.b64decode(packets[5]['result']['allocationBase64'])==expected(parse((folder/'consumer-input/1-source.swift').read_text()),64)
    failure=edits['lifecycle']['failures'][0]['record']['report'];assert failure['drained'] is True and failure['target_code']==2 and failure['remaining_observed']==0
    assert eof['packets']==[] and eof['lifecycle']['builds']==[] and len(eof['lifecycle']['failures'])==1
    assert eof['lifecycle']['channel']=={'accepted':1,'rejected':0,'cancelled':1,'writes':0,'closed':True,'reason':'input-ended'}
    report=eof['lifecycle']['failures'][0]['record']['report'];assert report['drained'] is True and report['remaining_observed']==0 and report['failure']=='abort' and report['target_code']==-15 # measured CLI wait; compiler phase unlocalized
    for source in [b'Text("unsupported")',b'A'*4097,b'\xff']:
        r=subprocess.run([sys.executable,str(folder/'runtime/tools/re/primary_oracle_cli.py')],input=source,capture_output=True,timeout=3);assert r.returncode==2 and not r.stdout
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode();return {'owned_processes':2,'fresh_modules':3,'complete_bytes':65536,'oracle_replays':6,'review':'pending'}
