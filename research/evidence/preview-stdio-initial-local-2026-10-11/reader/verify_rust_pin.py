"""Independent target/linker/source/drain receipt and full Rust-WASM allocation reader."""
import hashlib,json,subprocess,shutil
from pathlib import Path
from reloop.primarysource import parse,expected
from reloop.core import canonical_hash

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
    anchor=(folder/'fixture/manifest.json').read_bytes();assert sha(anchor)=='c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac'
    entries={r['path']:r for r in json.loads(anchor)['files']}
    config=json.loads((folder/'control/config.json').read_text());result=json.loads((folder/'control/live/result.json').read_text());facts=json.loads((folder/'control/result.json').read_text())
    toolchain=json.loads((folder/'control/toolchain.json').read_text());assert canonical_hash(toolchain['identity'])==toolchain['sha256']==config['toolchainPin']
    assert toolchain['identity']['compiler_file']['sha256']==config['rustcSha'] and toolchain['identity']['target']=='wasm32-wasip1'
    assert len(toolchain['identity']['target_files'])>0 and set(toolchain['identity']['linkers'])=={'rust-lld','gcc-ld/wasm-ld'}
    for row in list(toolchain['identity']['target_files'].values())+list(toolchain['identity']['linkers'].values()):assert row['bytes']>0 and len(row['sha256'])==64
    # Fresh reader hashes installed bytes independently of the inventory writer.
    def verify_file(path,row):
        h=hashlib.sha256();count=0
        with Path(path).open('rb') as stream:
            while True:
                b=stream.read(1048576)
                if not b:break
                count+=len(b);assert count<=268435456;h.update(b)
        assert count==row['bytes'] and h.hexdigest()==row['sha256']
    identity=toolchain['identity'];verify_file(identity['compiler'],identity['compiler_file'])
    libroot=Path(identity['target_libdir']);assert {str(p.relative_to(libroot)) for p in libroot.rglob('*') if p.is_file()}==set(identity['target_files'])
    for name,row in identity['target_files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        verify_file(Path(identity['target_libdir'])/name,row)
    host=next(x[6:] for x in identity['compiler_version'].splitlines() if x.startswith('host: '))
    linkdir=Path(identity['compiler']).parent.parent/'lib/rustlib'/host/'bin'
    for name,row in identity['linkers'].items():verify_file(linkdir/name,row)
    assert len(result['records'])==len(result['builds'])==3 and result['finalStatus']['liveWorkers']==0
    modules=[]
    for n,(row,build) in enumerate(zip(result['records'],result['builds'])):
        raw=(folder/'fixture'/('%d-source.swift'%n)).read_bytes();oracle=expected(parse(raw.decode()),64)
        for name in ['%d-source.swift'%n,'%d-expected.raw'%n]:
            b=(folder/'fixture'/name).read_bytes();assert len(b)==entries[name]['bytes'] and sha(b)==entries[name]['sha256']
        actual=(folder/'control/live'/('%d-frame.raw'%n)).read_bytes();assert actual==oracle==(folder/'fixture'/('%d-expected.raw'%n)).read_bytes() and len(actual)==16384
        receipt=build['receipt'];assert row['revision']==n+1 and row['sha256']==sha(actual) and row['sourceSha']==receipt['source_sha256']==sha(raw)
        assert receipt['toolchain_sha256']==toolchain['sha256']
        assert receipt['rustc_sha256']==config['rustcSha']==facts['compiler_sha256'] and receipt['config']==parse(raw.decode())
        stage=folder/'control/live'/build['stage']/'result';module=stage/'view.wasm';assert sha(module.read_bytes())==receipt['module_sha256']==row['moduleSha'];assert sha((stage/'module.rs').read_bytes())==receipt['generated_sha256']
        for name,pin in receipt['sources'].items():assert sha((folder/'frozen'/name).read_bytes())==pin
        report=build['execution']['report'];assert report['drained'] is True and report['target_code']==0 and report['remaining_observed']==0 and report['failure'] is None
        assert build['execution']['emergencyClosed'] is False and build['execution']['signal']=='SIGKILL'
        modules.append({'module':str(module),'expected':str(folder/'fixture'/('%d-expected.raw'%n)),'height':receipt['config']['height'],'width':receipt['config']['width']})
    assert len(result['failures'])==1;failure=result['failures'][0]['record'];assert failure['report']['drained'] is True and failure['report']['target_code']==2 and failure['emergencyClosed'] is False
    rejected=json.loads((folder/'control/unsupported.json').read_text());assert len(rejected)==22
    for row in rejected:
        try:parse(row['source'])
        except ValueError:pass
        else:raise AssertionError('Unsupported source accepted')
    negative=json.loads((folder/'negative.json').read_text());assert negative['code']==2 and negative['output_absent'] is True and 'Pinned Rust target/linker identity changed' in negative['error']
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(modules)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    return {'revisions':3,'bytes':49152,'unsupported':22,'review':'pending'}
