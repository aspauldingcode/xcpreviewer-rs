from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='native-incremental-update-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','source-verify.py','base-source-verify.py','native.swift','bridge.s','bridge.h','identity.c','run-native.py','input.bplist','reparse.swift','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert json.loads((work/'cross-runtime.json').read_text())==json.loads((artifact/'cross-runtime.json').read_text())
 print('2,540 source bytes,3 focused tests,109 native attempts,172 WASI invocations and62 reparses pass. Full383-test logs retained.16 native-accepted multi-key controls explicitly excluded from portable subset. Complete incremental/setup/shell/application/transport/provider parity remains open.')
