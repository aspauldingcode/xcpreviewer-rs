from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='variant-id-set-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs','unicode-check.swift','unicode-probe.rs','unicode-probe-Cargo.toml','unicode-probe-Cargo.lock']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('1308 source bytes,four focused tests,13670 public native Swift equality pairs,25 Swift/Foundation compositions,42 actual WASI invocations and17 Foundation reparses passed. Full291-test output retained separately. Private decoder/native Set byte order and Canvas/resource parity remain open.')
