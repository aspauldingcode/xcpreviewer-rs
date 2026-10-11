"""Independent file-generation, actual compiler/drain and full allocation evidence reader."""
import hashlib,json,subprocess,shutil,importlib.util
from pathlib import Path
from reloop.primarysource import parse,expected

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder)
    s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
    reader.verify(folder) # independent inventory rehash and original three revision bytes
    cfg=json.loads((folder/'control/config.json').read_text());d=json.loads((folder/'loops/result.json').read_text());modules=[]
    sources=[(folder/'fixture'/('%d-source.swift'%n)).read_bytes() for n in range(3)]
    oracles=[expected(parse(b.decode()),64) for b in sources]
    for mode in ['stale','close']:
        row=d[mode];root=folder/'loops'/mode
        assert row['observed']['identity'][2]==cfg['rustc'] and row['observed']['identity'][0]>0
        assert row['status']['liveWorkers']==row['status']['timers']==0 and row['status']['building'] is False and row['status']['loopClosed'] is True
        assert row['lateArtifactsStable'] is True and row['retainedRevision']==1
        assert (root/'baseline.raw').read_bytes()==oracles[0]
        final=(root/'final.raw').read_bytes();assert final==oracles[2 if mode=='stale' else 0] and sha(final)==row['finalSha']
        events=row['events'];published=[x for x in events if x['kind']=='published'];rejected=[x for x in events if x['kind']=='rejected']
        assert len(rejected)==1
        if mode=='stale':
            assert row['rejected'] is True and row['finalRevision']==2 and len(row['builds'])==3 and not row['failures']
            assert [x['revision'] for x in published]==[1,2] and 'Stale or foreign' in rejected[0]['error']
            assert published[1]['sourceSha256']==sha(sources[2]) and rejected[0]['generation']<published[1]['generation']
        else:
            assert row['closedSnapshotEmpty'] is True and row['drained'] is True and row['finalRevision']==1 and len(row['builds'])==len(row['failures'])==1
            assert [x['revision'] for x in published]==[1]
            failure=row['failures'][0]['record'];r=failure['report'];assert r['drained'] is True and r['remaining_observed']==0 and r['failure']=='abort' and r['target_code']==-15
            assert failure['emergencyClosed'] is False and failure['privateAbortRequested'] is True
        for n,build in enumerate(row['builds']):
            receipt=build['receipt'];src=sources[n if mode=='stale' else 0];assert receipt['source_sha256']==sha(src) and receipt['config']==parse(src.decode())
            assert receipt['toolchain_sha256']==cfg['toolchainPin'] and receipt['rustc_sha256']==cfg['rustcSha']
            report=build['execution']['report'];assert report['drained'] is True and report['failure'] is None and report['target_code']==report['remaining_observed']==0 and build['execution']['emergencyClosed'] is False
            stage=root/build['stage']/'result';module=stage/'view.wasm';assert sha(module.read_bytes())==receipt['module_sha256'];assert sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
            modules.append({'module':str(module),'expected':str(folder/'fixture'/('%d-expected.raw'%(n if mode=='stale' else 0))),'height':receipt['config']['height']})
        assert {x['stage'] for x in row['artifacts']}=={p.name for p in root.glob('build-*') if p.is_dir()}
        assert [x['present'] for x in row['artifacts']].count(False)==(1 if mode=='close' else 0)
        for artifact in row['artifacts']:
            p=root/artifact['stage']/'result/view.wasm';assert p.exists()==artifact['present'];assert artifact['sha']==(sha(p.read_bytes()) if p.exists() else None)
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    return {'controls':2,'bytes':65536,'modules':4,'review':'pending'}
