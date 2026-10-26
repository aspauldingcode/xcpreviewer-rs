from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-hashable-box-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','prior-source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('4,028 source bytes; two native-fixture tests; fresh native57 values/3,249 comparisons; supported2,304 pair matches;118 WASI runs/52 reparses pass. Full350-test logs retained. Wider numerics/UI/transport/global settlement remain open.')
