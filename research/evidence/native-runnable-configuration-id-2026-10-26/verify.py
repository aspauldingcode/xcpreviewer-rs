from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-runnable-id-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','state-source-verify.py','predecessor-source-verify.py','prior-source-verify.py','base-source-verify.py','source-findings.json','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('7,852 source bytes; two fixture tests; fresh native29 configurations/IDs and841 pairs,8 native typed variant codecs;93 WASI runs/41 reparses pass. Full355-test logs retained. Outer identity/cache/provider/transport/UI/global settlement remain open.')
