from pathlib import Path
import subprocess,tempfile,json,shutil,hashlib
artifact=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs')
subprocess.run(['python3',str(artifact/'source-verify.py')],cwd=r,check=True,timeout=30)
with tempfile.TemporaryDirectory(prefix='owned-service-xpc-replay-') as directory:
    work=Path(directory)
    for name in ['generate.rs','native.m','run.py']:shutil.copyfile(artifact/name,work/name)
    result=subprocess.run(['python3',str(work/'run.py')],cwd=r,capture_output=True,timeout=150)
    if result.returncode:print((result.stdout+result.stderr).decode())
    result.check_returncode();assert json.loads((work/'results.json').read_text())==json.loads((artifact/'results.json').read_text())
    for path,pin in json.loads((artifact/'fixtures.json').read_text()).items():
        file=work/'output'/Path(path).name;assert file.stat().st_size==pin['bytes'] and hashlib.sha256(file.read_bytes()).hexdigest()==pin['sha256']
    print('Four owned XPC request/reply outcomes match native UV observations and all captured fixture bytes. No private Swift connection invoked; no rights/resource settlement inferred.')
