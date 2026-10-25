from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='variants-reply-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('2228 source bytes,four group/payload tests,32 Foundation compositions,48 actual WASI invocations and16 Foundation reparses passed. Full302-test output retained separately. Private decoder/selection/rendering actions and Canvas/resource parity remain open.')
