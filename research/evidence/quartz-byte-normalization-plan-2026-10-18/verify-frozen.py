import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
for opt in [False,True]:
 p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/'test_models.py')],capture_output=True,text=True,timeout=15);p.check_returncode()
 p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/'analyze.py'),str(root.parent/'color-holdout-gate-recovery-2026-10-18')],capture_output=True,text=True,timeout=15);p.check_returncode()
 if json.loads(p.stdout)!=json.loads((root/'retrospective-result.json').read_text()):raise ValueError('diagnostic replay')
sys.path.insert(0,str(root))
from models import domain,predict
if domain()!=json.loads((root/'byte-domain-predictions.json').read_text()):raise ValueError('domain')
for model in ['division','reciprocal']:
 data=bytearray(b'\xa5'*16384)
 for y in range(3):
  for x in range(256):
   rgba=[x,(x+85*y+37)%256,(255-x+17*y)%256,255]
   data[y*4112+x*16:y*4112+x*16+16]=b''.join(predict(v,model) for v in rgba)
 if data!=(root/('prospective-'+model+'.raw')).read_bytes():raise ValueError('prospective buffer')
print(json.dumps({'verified':True,'sealed_files':len(seal['files']),'retrospective_bytes':12288,'prospective_native_execution':False,'native_cause_proven':False}))
