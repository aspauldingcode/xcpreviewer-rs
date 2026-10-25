from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='wrapper-properties-replay-') as directory:
    work=Path(directory)
    for name in ['check.py','source-verify.py','source-findings.json','format.swift','format-results.json','format.bplist','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
    p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
    if p.returncode:print((p.stdout+p.stderr).decode())
    p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
    print('Source,233 Rust tests, seven complete public Foundation formatting/presence/UTF-8 observations and actual WASI presentation replay passed. No private getter/full diagnostics/resource parity claim.')
