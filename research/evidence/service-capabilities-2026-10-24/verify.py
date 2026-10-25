from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='service-capabilities-replay-') as directory:
 work=Path(directory)
 for name in ['source-verify.py','source-findings.json','native.swift','native.bplist','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('2076 source bytes, three capability tests,15 public Foundation Bool controls and actual WASI passed. Full258-test output retained separately. Private decoder/delivery/XTP detection and Canvas/resource parity remain open.')
