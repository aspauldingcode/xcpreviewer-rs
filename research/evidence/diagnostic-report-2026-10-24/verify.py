from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='diagnostic-report-replay-') as directory:
 work=Path(directory)
 for name in ['source-verify.py','source-findings.json','native.swift','native.bplist','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('2288 source bytes, two report tests, five complete public Foundation controls and actual WASI passed. Full252-test run retained separately. Private collector/archive/resources remain open.')
