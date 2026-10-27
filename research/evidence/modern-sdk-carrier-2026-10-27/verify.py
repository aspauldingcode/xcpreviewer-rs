from pathlib import Path
import json,hashlib,subprocess,tempfile,shutil
r=Path(__file__).resolve().parents[3];e=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for f in json.loads((e/'seal.json').read_text())['files']:assert sha(e/f['path'])==f['sha256']
for p,h in json.loads((e/'implementation-pins.json').read_text()).items():assert sha(r/p)==h
w=Path(tempfile.mkdtemp(prefix='modern-sdk-replay-',dir='/private/tmp'))
for n in ['carrier.m','native.swift','bridge.h','bridge.s','identity.c','run-native.py','source-verify.py','run-wasi.cjs','check.py','input.bplist']:shutil.copy2(e/n,w/n)
p=subprocess.run(['python3',str(w/'check.py')],cwd=r,capture_output=True,timeout=180)
(w/'replay.stdout').write_bytes(p.stdout);(w/'replay.stderr').write_bytes(p.stderr);print(w);print(p.stdout.decode());p.check_returncode()
assert json.loads((w/'results.json').read_text())==json.loads((e/'results.json').read_text())
