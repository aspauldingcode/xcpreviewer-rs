"""Sealed Rust-WASM reader: independent Fraction bytes plus fresh runtime execution."""
import hashlib,json,subprocess,shutil
from pathlib import Path
from reloop.livecorpus import CLI_RUN,CLI_ANCHOR,NATIVE_RUN,NATIVE_ANCHOR
from reloop.primarysource import expected

def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink()
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    result=json.loads((folder/'control/result.json').read_text());index=json.loads((folder/'control/inputs/corpus.json').read_text());runtime=json.loads((folder/'control/runtime/result.json').read_text())
    assert index['pins']=={CLI_RUN:CLI_ANCHOR,NATIVE_RUN:NATIVE_ANCHOR}
    assert len(index['records'])==len(runtime['records'])==84;native=0
    for n,(row,receipt) in enumerate(zip(index['records'],runtime['records'])):
        data=(folder/'control/runtime'/('revision-%d.raw'%n)).read_bytes();oracle=expected(row['config'],row['stride'])
        assert len(data)==16384 and data==oracle==(folder/'control/inputs'/row['expected']).read_bytes()
        assert receipt['revision']==n+1 and receipt['allocation_sha256']==hashlib.sha256(data).hexdigest()
        assert receipt['module_sha256']==hashlib.sha256((folder/'control/inputs'/row['module']).read_bytes()).hexdigest()
        if row['native']:assert data==(folder/'control/inputs'/row['native']).read_bytes();native+=16384
    assert native==1310720 and runtime['final_status']['liveWorkers']==0
    assert [x['offset'] for x in runtime['faults']]==[0,52,16383]
    assert all(x['retained_revision']==7 and x['live_bytes']==16384 for x in runtime['faults'])
    for name,sha in result['sources'].items():assert hashlib.sha256((folder/'frozen'/name).read_bytes()).hexdigest()==sha
    assert result['observations']=={'rust_wasm_frames':84,'rust_wasm_bytes':1376256,'rust_wasm_native_bytes':1310720,'rust_wasm_faults':3,'rust_wasm_zero_workers':True,'rust_wasm_modules':len(result['modules'])}
    r=subprocess.run([shutil.which('node'),str(Path(__file__).with_suffix('.js')),str(folder)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr.decode()
    return {'frames':84,'bytes':1376256,'native_bytes':native,'invalid_strides':336,'growth_rejections':84,'review':'pending'}
