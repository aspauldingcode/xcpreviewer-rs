from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess
r=Path(__file__).resolve().parents[3];e=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in json.loads((e/'seal.json').read_text())['files']:assert sha(e/row['path'])==row['sha256']
for p,h in json.loads((e/'implementation-pins.json').read_text()).items():assert sha(r/p)==h
w=Path(tempfile.mkdtemp(prefix='swiftui-source-replay-',dir='/private/tmp'))
for n in ['check-capture.py','check-png.py','source-verify.py','run-native.py','native.swift','bridge.s','bridge.h','identity.c','build.py','check-packets.py','check-rust.py','run-wasi.cjs','worker-check.cjs','check.py']:shutil.copy2(e/n,w/n)
p=subprocess.run(['python3',str(w/'check.py')],cwd=r,capture_output=True,timeout=480);(w/'replay.stdout').write_bytes(p.stdout);(w/'replay.stderr').write_bytes(p.stderr);print(w,flush=True);print(p.stdout.decode(),flush=True);p.check_returncode()
assert json.loads((w/'results.json').read_text())==json.loads((e/'replay-results.json').read_text())
