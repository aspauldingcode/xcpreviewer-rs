from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='effective-overrides-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('4468 source bytes,three resolution tests,24 original public compositions,42 WASI runs and18 Foundation reparses pass. Full314-test output retained separately. Settings alignment/native selection/Canvas/resource parity remain open.')
