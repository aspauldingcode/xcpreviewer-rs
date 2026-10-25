from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='remote-prefix-replay-') as directory:
    work=Path(directory)
    for name in ['check.py','generate.swift','wasi.rs','run-wasi.cjs','observations.json','boundaries.bplist']:shutil.copyfile(artifact/name,work/name)
    p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
    if p.returncode:print((p.stdout+p.stderr).decode())
    p.check_returncode()
    assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
    print('Exhaustive public Swift scalar observations, complete table/golden fixture,223 Rust tests and actual WASI controls match. No private Swift decoder/resource settlement claim.')
