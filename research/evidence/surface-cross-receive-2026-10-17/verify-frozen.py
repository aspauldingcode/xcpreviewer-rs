"""Validate sealed owned evidence and compare every allocation; no native launch."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
for name,h in seal['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Seal mismatch: '+name)
sys.path.insert(0,str(p))
from admit import admitted
print(json.dumps({'sealed_files':len(seal['files']),'admission':admitted(p),'native_launched':False}))
