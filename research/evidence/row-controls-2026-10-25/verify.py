from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='row-controls-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs','probe.py']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();subprocess.run(['python3',str(work/'probe.py')],check=True,timeout=70);assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('3124 source bytes,three control-read/write tests,26 original public compositions,46 WASI runs and20 Foundation reparses pass. Full329-test output retained separately. Private bindings/animation/default spelling/persistence/Canvas/resource parity remain open.')
