from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
subprocess.run(['python3',str(artifact/'source-verify.py')],check=True,timeout=80)
with tempfile.TemporaryDirectory(prefix='human-error-replay-') as directory:
    work=Path(directory)
    for name in ['check.py','source-verify.py','source-findings.json','native.swift','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
    p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
    if p.returncode:print((p.stdout+p.stderr).decode())
    p.check_returncode()
    assert json.loads((work/'native.stdout').read_text())==json.loads((artifact/'native.stdout').read_text())
    assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
    print('Eight Foundation cast controls,216 Rust tests and actual WASI projection/extraction replay passed; private callback and native settlement remain open.')
