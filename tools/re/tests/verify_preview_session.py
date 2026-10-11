"""Independent local consumer descriptor, build/drain and allocation reader."""
import hashlib,importlib.util,json,subprocess,shutil
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    sha=lambda b:hashlib.sha256(b).hexdigest();d=json.loads((folder/'session/result.json').read_text());cfg=json.loads((folder/'consumer-config.json').read_text());states=d['states'];assert len(states)==4 and len(d['controls'])==8 and len(set(d['controls']))==8
    assert len(d['builds'])==3 and len(d['failures'])==1
    sources=[(folder/'consumer-input'/f'{i}-source.swift').read_bytes() for i in range(3)];original=[(folder/'fixture'/f'{i}-source.swift').read_bytes() for i in range(3)]
    assert sources[0]==original[0] and sources[2]==original[2] and sources[1]==original[1].replace(b'width: 13, height: 7',b'width: 9, height: 5')
    modules=[]
    for i,build in enumerate(d['builds']):
        oracle=expected(parse(sources[i].decode()),64);assert oracle==(folder/'consumer-input'/f'{i}-expected.raw').read_bytes()==(folder/'session'/f'{i}-frame.raw').read_bytes()
        receipt=build['receipt'];config=parse(sources[i].decode());assert receipt['config']==config and receipt['source_sha256']==sha(sources[i]) and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
        report=build['execution']['report'];assert report['drained'] is True and report['target_code']==report['remaining_observed']==0 and report['failure'] is None and build['execution']['emergencyClosed'] is False
        stage=folder/'session'/build['stage']/'result';module=stage/'view.wasm';assert sha(module.read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
        state=states[[0,1,3][i]];frame=state['frame'];assert state['schemaVersion']==1 and set(state)=={'schemaVersion','scope','lifecycle','frame','diagnostics'}
        assert frame=={'revision':i+1,'generation':[1,2,4][i],'sourceSha256':sha(sources[i]),'moduleSha256':receipt['module_sha256'],'allocationSha256':sha(oracle),'allocationBytes':16384,'renderedBytes':64*config['height'],'width':config['width'],'height':config['height'],'stride':64,'format':'premultiplied-RGBA8'}
        assert state['diagnostics']['retainedEvents']<=64 and 'stderr' not in json.dumps(state) and 'toolchainPin' not in json.dumps(state)
        modules.append({'module':str(module),'expected':str(folder/'consumer-input'/f'{i}-expected.raw'),'height':config['height']})
    assert states[2]['frame']==states[1]['frame'] and states[2]['diagnostics']['lastFailure']['kind']=='rejected' and states[2]['diagnostics']['lastFailure']['generation']==3
    assert len(states[2]['diagnostics']['lastFailure']['error'].encode())<=512
    assert (folder/'session/retained.raw').read_bytes()==expected(parse(sources[1].decode()),64)
    failure=d['failures'][0]['record'];assert failure['report']['target_code']==2 and failure['report']['drained'] is True and failure['report']['remaining_observed']==0
    final=d['final'];assert final['frame'] is None and final['lifecycle']['liveWorkers']==final['lifecycle']['timers']==0 and final['lifecycle']['building'] is False and final['lifecycle']['loopClosed'] is True
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode();return {'fresh_modules':3,'consumer_controls':8,'complete_bytes':65536,'review':'pending'}
