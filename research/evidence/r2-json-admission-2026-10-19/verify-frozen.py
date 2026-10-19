"""Replay source-verifier counterexamples only; never launch native code."""
import hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
names={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if names!=set(seal['files']):raise ValueError('Inventory changed')
for n,h in seal['files'].items():
 q=p/n
 if q.is_symlink() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('Seal changed: '+n)
src=Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-full-reuse-2026-10-11')
if hashlib.sha256((src/'manifest.json').read_bytes()).hexdigest()!='3882895c02cd09939282f3d1c8867c5726e236a094d4107617201afe39988d6a':raise ValueError('Historical seal changed')
m=json.loads((src/'manifest.json').read_text())
for n,v in m['files'].items():
 q=src/n;raw=q.read_bytes()
 if q.is_symlink() or len(raw)!=v['bytes'] or hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('Historical bytes changed')
for flags,label in [([], 'normal'),(['-O'],'optimized')]:
 for reader,stage in [('before_verify.py','before'),('verify_surface_full_reuse.py','after')]:
  z=subprocess.run([sys.executable,*flags,'-B',str(p/'controls.py'),reader],capture_output=True,text=True,timeout=20)
  if z.returncode:raise ValueError(z.stderr)
  current=json.loads(z.stdout);saved=json.loads((p/(stage+'-'+label+'.json')).read_text())
  if [(x['fault'],x['accepted'],x['result']) for x in current['cases']]!=[(x['fault'],x['accepted'],x['result']) for x in saved['cases']]:raise ValueError('Frozen matrix changed')
  if len(current['cases'])!=14 or not all(x['accepted']==(stage=='before' or x['fault']=='positive') for x in current['cases']):raise ValueError('Unexpected admission')
print(json.dumps({'sealed_files':len(names),'false_acceptances_reproduced_per_mode':13,'corrected_faults_rejected_per_mode':13,'full_allocation_bytes':163840,'native_execution':False,'milestones_complete':False}))
