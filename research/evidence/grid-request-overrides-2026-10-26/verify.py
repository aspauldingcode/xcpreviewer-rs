from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='grid-overrides-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('1812 source bytes,three focused tests,32 public compositions,58 WASI runs and26 reparses pass. Full338-test output retained. Private previewRequests/mode fallback/full request/runtime/transport/Canvas/resource parity remain open.')
