"""Validate stored owned transport receipts only; no socket/native acquisition."""
from pathlib import Path
import hashlib,json,sys,subprocess
p=Path(__file__).resolve().parent;s=json.loads((p/'seal.json').read_text())
names={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if names!=set(s['files']):raise ValueError('Evidence inventory changed')
for n,h in s['files'].items():
 q=p/n
 if q.is_symlink() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('Seal changed: '+n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h:raise ValueError('Reviewed source changed')
sys.path.insert(0,str(p))
from admit import admit
result=admit(p)
q=subprocess.run([sys.executable,'-B',str(p/'test-admission.py')],capture_output=True,text=True,timeout=10)
if q.returncode:raise ValueError(q.stderr)
print(json.dumps({'sealed_files':len(names),**result,'new_socket_execution':False}))
