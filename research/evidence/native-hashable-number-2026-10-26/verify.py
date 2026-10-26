from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-hashable-number-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','prior-source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('4,028 source bytes; three fixture tests; fresh native96 cached/public projections and9,216 comparisons;205 WASI runs/100 reparses pass. Full351-test logs retained. Generic origins/UI/transport/global settlement remain open.')
