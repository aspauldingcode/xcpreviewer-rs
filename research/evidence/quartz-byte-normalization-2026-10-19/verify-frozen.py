"""Replay sealed public-oracle evidence only; no native acquisition."""
from pathlib import Path
import hashlib,json,sys,importlib.util
p=Path(__file__).resolve().parent;s=json.loads((p/'seal.json').read_text())
names={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.name!='seal.json'}
if names!=set(s['files']):raise ValueError('Evidence inventory changed')
for n,h in s['files'].items():
 q=p/n
 if q.is_symlink() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('Seal changed: '+n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h:raise ValueError('Approved source changed')
sys.path.insert(0,str(p))
from admit import admitted
from historical_compare import compare,BASE
v=admitted(p);history=compare();saved=json.loads((p/'result.json').read_text())
if v!=saved['admission'] or history!=saved['historical_predeclared_comparison']:raise ValueError('Result changed')
if not all(x['provider_matches'] is True and x['readback_mismatch_bytes']==0 and x['readback_length']==4096 for x in history['predeclared_reciprocal_comparison']):raise ValueError('Historical model rejected')
rea=json.loads((p/'rea-identity.json').read_text())
if rea['artifact']['sha256']!=saved['binary_sha256'] or rea['artifact']['architecture']!='arm64' or rea['server_identity']['alignment']['state']!='aligned':raise ValueError('Artifact binding changed')
spec=importlib.util.spec_from_file_location('historical_strict_export',BASE/'export/admit.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
try:old.admitted(BASE/'export')
except ValueError:old_rejected=True
else:old_rejected=False
if not old_rejected:raise ValueError('Historical rejection changed')
print(json.dumps({'sealed_files':len(names),'admission':v,'historical_reciprocal_bytes_compared':30084,'old_strict_export_still_rejects':old_rejected,'native_launched':False}))
