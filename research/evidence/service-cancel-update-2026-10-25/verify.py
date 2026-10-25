from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='cancel-update-replay-') as directory:
 work=Path(directory)
 for name in ['source-verify.py','source-findings.json','native.swift','native.bplist','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('1228 source bytes, three UInt64/cancel tests,10 Foundation seed controls and7 Foundation cross-parses and actual WASI passed. Full264-test output retained separately. Private decoder/cancellation and Canvas/resource parity remain open.')
