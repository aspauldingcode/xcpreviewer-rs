"""Independent sealed reader and actual dual-runtime checker execution."""
import hashlib,json,shutil,subprocess
from pathlib import Path
from reloop.primarysource import expected
from reloop.portable import TOOLCHAIN
from reloop.wasmkit import parse_result
from reloop.livecorpus import CLI_RUN,CLI_ANCHOR,NATIVE_RUN,NATIVE_ANCHOR

def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    assert set(manifest['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in manifest['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink()
        b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
    d=json.loads((folder/'control/result.json').read_text());index=json.loads((folder/'rust-wasm/inputs/corpus.json').read_text())
    assert index['pins']=={CLI_RUN:CLI_ANCHOR,NATIVE_RUN:NATIVE_ANCHOR}
    assert len(d['rows'])==42 and len(d['abi'])==26 and hashlib.sha256((TOOLCHAIN/'wasmkit').read_bytes()).hexdigest()==d['runtime_sha256']
    assert hashlib.sha256((folder/'frozen/wasm-checker.rs').read_bytes()).hexdigest()==d['checker_source_sha256']
    for row in d['abi']:
        assert row['capacity']==16384 and parse_result(row['capacity_stdout'])==16384
        assert 0<=row['pointer']<=131072-16384 and parse_result(row['pointer_stdout'])==row['pointer']
        for export,value in [('capacity',row['capacity']),('pixels',row['pointer'])]:
            r=subprocess.run([str(TOOLCHAIN/'wasmkit'),'run',str(folder/'rust-wasm/inputs'/row['module']),export],capture_output=True,timeout=3)
            assert r.returncode==0 and parse_result(r.stdout.decode())==value
    for n,(row,reference) in enumerate(zip(d['rows'],index['records'][::2])):
        assert row['job']==n and row['config']==reference['config'] and row['stride']==reference['stride']
        oracle=expected(row['config'],row['stride']);assert oracle==(folder/'rust-wasm/inputs'/reference['expected']).read_bytes() and len(oracle)==16384
        if reference['native']:assert oracle==(folder/'rust-wasm/inputs'/reference['native']).read_bytes()
        assert row['rendered']==row['stride']*row['config']['height'] and parse_result(row['render_stdout'])==row['rendered']
        original=folder/'rust-wasm/inputs'/reference['module'];r=subprocess.run([str(TOOLCHAIN/'wasmkit'),'run',str(original),'render','i32:'+str(row['stride'])],capture_output=True,timeout=3);assert r.returncode==0 and parse_result(r.stdout.decode())==row['rendered']
        module=folder/'control'/row['module'];assert hashlib.sha256(module.read_bytes()).hexdigest()==row['module_sha256']
        assert [c['mutation'] for c in row['controls']]==list(range(5)) and row['v8']==[0,1,1,1,0]
        for c,value in zip(row['controls'],[0,1,1,1,0]):
            assert c['mismatches']==value and parse_result(c['stdout'])==value
            r=subprocess.run([str(TOOLCHAIN/'wasmkit'),'run',str(module),'verify','i32:'+str(c['mutation'])],capture_output=True,timeout=3);assert r.returncode==0 and parse_result(r.stdout.decode())==value
    script=Path(__file__).with_suffix('.js');r=subprocess.run([shutil.which('node'),str(script),str(folder)],capture_output=True,timeout=15);assert r.returncode==0,r.stderr.decode()
    assert d['observations']=={'rust_second_jobs':42,'rust_second_controls':210,'rust_second_compared_bytes':3440640,'rust_second_mutants':126,'rust_second_abi_modules':26,'rust_second_all_equal':True}
    return {'jobs':42,'controls':210,'full_compared_bytes':3440640,'review':'pending'}
