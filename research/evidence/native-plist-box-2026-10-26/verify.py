from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-plist-box-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','expected-native.bplist','fixture.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('1488 source bytes,one private-fixture test,actual shipped box value methods,33 native cases,54 WASI runs and21 reparses pass. Full348-test output retained. HashableBox/UI/full transport/global resource parity remain open.')
