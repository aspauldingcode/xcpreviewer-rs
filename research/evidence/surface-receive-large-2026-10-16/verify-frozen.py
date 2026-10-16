"""Offline replay only: no subprocess or native launch."""
import hashlib,json
from pathlib import Path
from admit import admitted,need
p=Path(__file__).parent;s=json.loads((p/'seal.json').read_text())
for n,h in s['files'].items():need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h)
reports=[admitted(p/n) for n in ['first','repeat']]
for mode in ['control','large']:
 for n in ['before.bin','after-small.bin','received.bin','alias-after-cleanup.bin']:need((p/'first/owned-documents'/mode/n).read_bytes()==(p/'repeat/owned-documents'/mode/n).read_bytes())
need(reports[0]==reports[1]);print(json.dumps({'frozen_runs_admitted':2,'full_bytes_compared':sum(v['full_bytes_compared'] for v in reports),'native_launched':False}))
