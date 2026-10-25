from pathlib import Path
import subprocess,tempfile,json,shutil,os,sys,hashlib
artifact=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');bin=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
sys.path.insert(0,str(r/'tools/re'));from reloop.cachebind import Cache
cache=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');pins=json.loads((artifact/'target-identities.json').read_text());assert hashlib.sha256(cache.read(0x263300000,0x10440)).hexdigest()==pins['services_text_sha256'];assert cache.exports(0x263300000)[1]==pins['services_uuid'];assert cache.exports(0x181d9e000)[1]==pins['foundation_uuid']
with tempfile.TemporaryDirectory(prefix='plist-writer-replay-') as directory:
    work=Path(directory)
    for name in ['generate.rs','native.swift','validate.py']:shutil.copyfile(artifact/name,work/name)
    env=dict(os.environ,RUSTC=str(bin/'rustc'),RUSTDOC=str(bin/'rustdoc'))
    build=subprocess.run([str(bin/'cargo'),'build','--offline','--manifest-path','tools/re/rust/canvas-core/Cargo.toml','--target-dir',str(work/'target')],cwd=r,env=env,capture_output=True,timeout=60);build.check_returncode()
    run=subprocess.run(['python3',str(work/'validate.py')],cwd=r,capture_output=True,timeout=75)
    if run.returncode:print((run.stdout+run.stderr).decode())
    run.check_returncode();assert json.loads((work/'results.json').read_text())==json.loads((artifact/'results.json').read_text())
    negative=work/'negative';negative.mkdir();shutil.copyfile(artifact/'data-root-initial.bplist',negative/'data.bplist')
    result=subprocess.run([str(work/'native'),str(negative)],capture_output=True,timeout=5,check=True)
    rows=json.loads(result.stdout);assert len(rows)==1 and rows[0]['code']==3840
    print('Foundation matched15 generated outputs; original narrow-offset root-data fixture still rejects with3840. Owned binaries/cache removed; no private callback invoked.')
