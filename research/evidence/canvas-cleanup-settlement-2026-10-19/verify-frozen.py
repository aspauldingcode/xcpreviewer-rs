"""Verify/replay callback feasibility only; no native UI APIs."""
from pathlib import Path
import hashlib,json,sys,tempfile,shutil,subprocess
p=Path(__file__).resolve().parent;s=json.loads((p/'seal.json').read_text())
names={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if names!=set(s['files']):raise ValueError('Evidence inventory changed')
for n,h in s['files'].items():
 q=p/n
 if q.is_symlink() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('Seal changed: '+n)
sys.path.insert(0,str(p))
from admit import admit
expected=admit(p)
with tempfile.TemporaryDirectory(prefix='cleanup-settlement-replay-') as d:
 replay=Path(d)/'e';shutil.copytree(p,replay,ignore=shutil.ignore_patterns('__pycache__'))
 q=subprocess.run([sys.executable,'-B',str(replay/'run-controls.py')],capture_output=True,text=True,timeout=15)
 if q.returncode:raise ValueError(q.stderr)
 if admit(replay)!=expected:raise ValueError('Replay mismatch')
print(json.dumps({'sealed_files':len(names),**expected}))
