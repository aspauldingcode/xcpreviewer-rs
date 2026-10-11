"""Independent successful-completion publication veto and full-byte reader."""
import hashlib,importlib.util,json,subprocess,shutil
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
    folder=Path(folder)
    s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    d=json.loads((folder/'completion/result.json').read_text());cfg=json.loads((folder/'control/config.json').read_text());assert [r['mode'] for r in d['controls']]==['close','supersede']
    sources=[(folder/'fixture'/f'{i}-source.swift').read_bytes() for i in range(3)];oracles=[expected(parse(b.decode()),64) for b in sources]
    sha=lambda b:hashlib.sha256(b).hexdigest();modules=[]
    for row in d['controls']:
        root=folder/'completion'/row['mode'];assert row['boundary']=={'phase':'oracle-after-successful-execution','revision':1,'frameMatchesBaseline':True}
        assert row['closedSnapshotEmpty'] is True and not row['failures']
        status=row['status'];assert status['loopClosed'] is True and status['building'] is False and status['liveWorkers']==status['timers']==0
        assert (root/'baseline.raw').read_bytes()==oracles[0]
        close=row['mode']=='close';events=row['events'];pub=[e for e in events if e['kind']=='published'];reject=[e for e in events if e['kind']=='rejected']
        assert [e['generation'] for e in pub]==([1] if close else [1,3]);assert [e['revision'] for e in pub]==([1] if close else [1,2])
        assert len(reject)==1 and reject[0]['generation']==2 and ('File loop closed before publication' if close else 'Stale or foreign build ticket') in reject[0]['error']
        if not close:assert (root/'final.raw').read_bytes()==oracles[2] and pub[-1]['sourceSha256']==sha(sources[2])
        assert len(row['builds'])==(2 if close else 3)
        for i,build in enumerate(row['builds']):
            receipt=build['receipt'];assert receipt['source_sha256']==sha(sources[i]) and receipt['config']==parse(sources[i].decode())
            assert receipt['toolchain_sha256']==cfg['toolchainPin'] and receipt['rustc_sha256']==cfg['rustcSha']
            report=build['execution']['report'];assert report['drained'] is True and report['target_code']==0 and report['failure'] is None and report['remaining_observed']==0
            assert build['execution']['emergencyClosed'] is False
            stage=root/build['stage'];assert (stage/'source.swift').read_bytes()==sources[i]
            module=stage/'result/view.wasm';assert sha(module.read_bytes())==receipt['module_sha256'] and sha((stage/'result/module.rs').read_bytes())==receipt['generated_sha256']
            modules.append({'module':str(module),'expected':str(folder/'fixture'/f'{i}-expected.raw'),'height':receipt['config']['height']})
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    return {'controls':2,'fresh_modules':5,'full_bytes':81920,'review':'pending'}
