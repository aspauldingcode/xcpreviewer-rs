from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='full-diagnostics-replay-') as directory:
 work=Path(directory)
 for name in ['source-verify.py','source-findings.json','native.swift','native.bplist','native-results.json','boundaries.swift','boundaries.json','boundaries.bplist','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=240)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('1656 source bytes,241 Rust tests,nine full public Foundation reports,1112064 scalar boundaries and actual WASI diagnostics passed. Private getter execution/collection and resource settlement remain open.')
