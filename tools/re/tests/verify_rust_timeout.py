"""Independent failed-build phase, wait/drain, recovery and allocation reader."""
import hashlib,json,subprocess,shutil,importlib.util
from pathlib import Path
from reloop.primarysource import parse,expected

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('file_reader',Path(__file__).with_name('verify_rust_file.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    cfg=json.loads((folder/'control/config.json').read_text());d=json.loads((folder/'failures/result.json').read_text());assert [r['mode'] for r in d['controls']]==['deadline','pin','oracle'];modules=[]
    sources=[(folder/'fixture'/('%d-source.swift'%n)).read_bytes() for n in range(3)];oracles=[expected(parse(b.decode()),64) for b in sources]
    def module(stage,receipt,n):
        assert receipt['source_sha256']==sha(sources[n]) and receipt['config']==parse(sources[n].decode()) and receipt['rustc_sha256']==cfg['rustcSha'] and receipt['toolchain_sha256']==cfg['toolchainPin']
        assert sha((stage/'view.wasm').read_bytes())==receipt['module_sha256'] and sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
        for name,pin in receipt['sources'].items():assert sha((folder/'frozen'/name).read_bytes())==pin
        modules.append({'module':str(stage/'view.wasm'),'expected':str(folder/'fixture'/('%d-expected.raw'%n)),'height':receipt['config']['height']})
    for row in d['controls']:
        root=folder/'failures'/row['mode'];assert row['retainedRevision']==1 and row['recoveryRevision']==2 and row['lateArtifactsStable'] is True
        assert (root/'baseline.raw').read_bytes()==(root/'retained.raw').read_bytes()==oracles[0];assert sha(oracles[0])==row['retainedSha'];assert (root/'recovery.raw').read_bytes()==oracles[2] and sha(oracles[2])==row['recoverySha']
        assert row['status']['loopClosed'] is True and row['status']['liveWorkers']==row['status']['timers']==0 and row['status']['building'] is False
        published=[e for e in row['events'] if e['kind']=='published'];rejected=[e for e in row['events'] if e['kind']=='rejected'];assert [(e['generation'],e['revision']) for e in published]==[(1,1),(3,2)] and len(rejected)==1 and rejected[0]['generation']==2
        assert len(row['builds'])==2 and row['failedBuilds']==[]
        for n,build in zip([0,2],row['builds']):
            r=build['execution']['report'];assert r['drained'] is True and r['remaining_observed']==r['target_code']==0 and r['failure'] is None and build['execution']['emergencyClosed'] is False
            module(root/'normal'/build['stage']/'result',build['receipt'],n)
        failure=row['failure'];execution=failure['record'];r=execution['report'];assert r['drained'] is True and r['remaining_observed']==0 and execution['emergencyClosed'] is False
        assert any(x['pid']>0 and x['parent']==execution['pid'] and len(x['identity'])==3 and x['identity'][2].startswith('/') for x in row['observations'])
        if row['mode']=='deadline':assert r['failure']=='deadline' and r['target_code']==-15
        elif row['mode']=='pin':assert r['target_code']==2 and 'Pinned Rust target/linker identity changed' in execution['stderr']
        else:assert r['target_code']==0 and r['failure'] is None and 'Owned independent oracle rejection' in failure['error']
        assert len(row['artifacts'])==1 and {x['stage'] for x in row['artifacts']}=={p.name for p in (root/'failure').glob('build-*') if p.is_dir()}
        artifact=row['artifacts'][0];stage=root/'failure'/artifact['stage'];assert json.loads((stage/'failure.json').read_text())==failure
        p=stage/'result/view.wasm';assert artifact['present']==p.exists()==(row['mode']=='oracle') and artifact['sha']==(sha(p.read_bytes()) if p.exists() else None)
        if row['mode']=='oracle':module(stage/'result',json.loads(execution['stdout']),1)
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    return {'controls':3,'bytes':147456,'modules':7,'review':'pending'}
