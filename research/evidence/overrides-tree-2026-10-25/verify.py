from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='overrides-tree-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','source-findings.json','native.swift','native.bplist','reparse.swift','run-wasi.cjs','dictionary-probe.swift','collision.swift','collision0.bplist','collision1.bplist','collision-tree0.bplist','collision-tree1.bplist']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('3352 source bytes,four override tree tests,28 Foundation compositions,43 actual WASI invocations and13 Foundation reparses passed, including2 explicit raw-key policy differences. Full298-test output retained separately. Private decoder/selection/rendering actions and Canvas/resource parity remain open.')
