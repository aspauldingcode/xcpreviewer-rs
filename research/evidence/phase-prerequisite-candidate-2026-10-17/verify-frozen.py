import hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
s=json.loads((p/'seal.json').read_text())
for name,h in s['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Seal mismatch: '+name)
x=subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),'-B',str(p/'test_phase_prerequisites.py')],capture_output=True,text=True,timeout=15)
if x.returncode:raise ValueError(x.stderr)
sys.path.insert(0,str(p))
from phase_prerequisites import receipt
v=json.loads((p/'prior-summary.json').read_text())['experiments']['half']
for phase in ['compile','output-valid']:receipt(p/'prior-receipts',phase,v['source_sha256'],v['binary_sha256'])
print(json.dumps({'files_verified':len(s['files']),'synthetic_methods':5,'prior_receipts_admitted':True,'native_launched':False,'independent_review':'pending'}))
