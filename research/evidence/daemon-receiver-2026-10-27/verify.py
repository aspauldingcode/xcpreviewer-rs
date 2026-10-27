from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess
r=Path(__file__).resolve().parents[3];e=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in json.loads((e/'seal.json').read_text())['files']:assert sha(e/row['path'])==row['sha256']
for p,h in json.loads((e/'implementation-pins.json').read_text()).items():assert sha(r/p)==h
w=Path(tempfile.mkdtemp(prefix='daemon-receiver-replay-',dir='/private/tmp'))
for n in ['native.swift','bridge.h','bridge.s','identity.c','carrier.m','run-native.py','input.bplist','check.py','run-wasi.cjs','source-verify.py']:shutil.copy2(e/n,w/n)
p=subprocess.run(['python3',str(w/'check.py'),'--replay'],cwd=r,capture_output=True,timeout=180);(w/'replay.stdout').write_bytes(p.stdout);(w/'replay.stderr').write_bytes(p.stderr);print(w,flush=True);print(p.stdout.decode(),flush=True);p.check_returncode()
a=json.loads((w/'results.json').read_text());b=json.loads((e/'results.json').read_text());assert a.pop('rust_tests')==2;assert b.pop('rust_tests')==405;assert a==b
