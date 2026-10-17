import hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent;s=json.loads((p/'seal.json').read_text())
for name,h in s['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Seal mismatch: '+name)
args=[sys.executable,*(['-O'] if sys.flags.optimize else []),'-B']
a=subprocess.run(args+[str(p/'endpoints/admit.py')],capture_output=True,text=True,timeout=10)
if a.returncode:raise ValueError(a.stderr)
b=subprocess.run(args+[str(p/'gray/admit.py')],capture_output=True,text=True,timeout=10)
if b.returncode==0 or 'ValueError' not in b.stderr:raise ValueError('Gray failure was not retained')
c=subprocess.run(args+[str(p/'gray/diagnose-frozen.py'),'--verify-only'],capture_output=True,text=True,timeout=10)
if c.returncode:raise ValueError(c.stderr)
print(json.dumps({'files_verified':len(s['files']),'endpoint_accepted':True,'gray_rejected':True,'native_launched':False}))
