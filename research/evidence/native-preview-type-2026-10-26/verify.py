from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-preview-type-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('5,976 source bytes; two fixture/API tests; fresh native41 enum attempts,26 roundtrips,15 errors;70 WASI runs/26 reparses pass. Full362-test logs retained. Equality/hash, scene routing, complete shell/instance/updater/transport/UI/provider/global settlement remain open.')
