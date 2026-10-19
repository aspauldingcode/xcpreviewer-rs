"""Replay recorded scalar conformance only; no engine/native execution."""
from pathlib import Path
import hashlib,json,sys
p=Path(__file__).resolve().parent;s=json.loads((p/'seal.json').read_text())
names={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if names!=set(s['files']):raise ValueError('Inventory changed')
for n,h in s['files'].items():
 q=p/n
 if q.is_symlink() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('Seal changed: '+n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h:raise ValueError('Approved source changed')
sys.path.insert(0,str(p))
from admit import admit
v=admit(p)
if v!=json.loads(json.loads((p/'admit.py.normal.json').read_text())['stdout']):raise ValueError('Result changed')
print(json.dumps({'sealed_files':len(names),**v,'new_engine_execution':False}))
