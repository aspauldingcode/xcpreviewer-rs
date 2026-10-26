from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-configuration-controls-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','state-source-verify.py','predecessor-source-verify.py','prior-source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('7,504 source bytes and52 key-path pattern bytes; two fixture/API tests;29 actual native key-path getter calls across24 state sequences after source-wrapper destruction;56 WASI runs/25 reparses pass. Full360-test logs retained. Full behavior getter/downstream routing/transport/UI/provider/global settlement remain open.')
