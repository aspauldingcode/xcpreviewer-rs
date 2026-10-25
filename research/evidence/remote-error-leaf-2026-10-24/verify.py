from pathlib import Path
import tempfile,shutil,subprocess,json,hashlib
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='remote-leaf-replay-') as directory:
    work=Path(directory)
    for name in ['check.py','source-verify.py','source-findings.json','native.swift','generate.rs','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
    p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
    if p.returncode:print((p.stdout+p.stderr).decode())
    p.check_returncode()
    assert json.loads((work/'native.stdout').read_text())==json.loads((artifact/'native.stdout').read_text())
    assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
    for name,pin in json.loads((artifact/'fixtures.json').read_text()).items():
        file=work/'output'/name;assert file.stat().st_size==pin['bytes'] and hashlib.sha256(file.read_bytes()).hexdigest()==pin['sha256']
    print('Source checks,222 Rust tests, four Foundation wire dictionaries and actual WASI leaf execution replay passed. Private decoder/runtime and resource settlement remain open.')
