from pathlib import Path
import tempfile,subprocess,shutil,json,hashlib
r=Path(__file__).resolve().parents[3];e=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for f in json.loads((e/'seal.json').read_text())['files']:assert sha(e/f['path'])==f['sha256']
for f,h in json.loads((e/'implementation-pins.json').read_text()).items():assert sha(r/f)==h
w=Path(tempfile.mkdtemp(prefix='service-factory-replay-',dir='/private/tmp'))
for n in ['bridge.s','bridge.h','identity.c','native.swift','peer-outgoing.m','peer-incoming.m','baseline.m','check.py','source-verify.py']:shutil.copy2(e/n,w/n)
p=subprocess.run(['python3',str(w/'check.py')],cwd=r,capture_output=True,timeout=90)
(w/'replay.stdout').write_bytes(p.stdout);(w/'replay.stderr').write_bytes(p.stderr);print(w);print(p.stdout.decode());p.check_returncode()
