"""Offline seal and independent consumer replay; no native launch or writes."""
import hashlib,json
from pathlib import Path
from admit import admitted,need
p=Path(__file__).parent;s=json.loads((p/'seal.json').read_text())
for n,h in s['files'].items():need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h)
print(json.dumps({'native_launched':False,'admission':admitted(p)}))
