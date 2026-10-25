from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-error-replay-') as directory:
 work=Path(directory)
 for name in ['source-verify.py','source-findings.json','native.m','native-results.json','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 shutil.copytree(artifact/'output',work/'output')
 for name in ['source-verify.py','check.py']:
  p=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=180)
  if p.returncode:print((p.stdout+p.stderr).decode())
  p.check_returncode()
 assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('548 source bytes,237 Rust tests,four complete native factory controls and actual WASI error pipeline passed; Swift conversion and resource settlement remain open.')
