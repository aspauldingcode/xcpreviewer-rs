"""Replay sealed evidence only; never launch native processes."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
actual={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if actual!=set(seal['files']):raise ValueError('Evidence inventory mismatch')
for name,h in seal['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Seal mismatch: '+name)
sys.path.insert(0,str(p))
from admit import admitted
v=admitted(p)
if v!=json.loads((p/'result.json').read_text())['independent_admission']:raise ValueError('Result mismatch')
pins=json.loads((p/'approved-pins.json').read_text())
for name,h in pins.items():
 if hashlib.sha256((p/name).read_bytes()).hexdigest()!=h:raise ValueError('Approved pin mismatch')
rea=json.loads((p/'rea-identity.json').read_text())
if rea['artifact']['sha256']!=json.loads((p/'compile-record.json').read_text())['binary_sha256'] or rea['artifact']['architecture']!='arm64' or rea['server_identity']['alignment']['state']!='aligned':raise ValueError('Artifact binding mismatch')
print(json.dumps({'sealed_files':len(seal['files']),'admission':v,'native_launched':False}))
