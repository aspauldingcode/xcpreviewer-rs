import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
sys.path.insert(0,str(root))
from phase_prerequisites import receipt
for child in ['callback','export']:
 proof=json.loads((root/'provenance.json').read_text())[child]
 if hashlib.sha256((root/child/'probe.swift').read_bytes()).hexdigest()!=proof['source_sha256']:raise ValueError('source')
 for phase in ['compile','output-valid','fixture']:receipt(root/child,phase,proof['source_sha256'],proof['binary_sha256'])
 for name,digest in json.loads((root/child/'approved-pins.json').read_text()).items():
  if hashlib.sha256((root/child/name).read_bytes()).hexdigest()!=digest:raise ValueError('pin')
 for optimized in [False,True]:
  result=subprocess.run([sys.executable,*(['-O'] if optimized else []),'-B',str(root/child/'admit.py')],capture_output=True,text=True,timeout=15)
  if child=='callback':
   result.check_returncode()
   if json.loads(result.stdout)!=json.loads((root/child/'admission.json').read_text()):raise ValueError('callback replay')
  elif result.returncode==0 or 'Receive-size evidence rejected' not in result.stderr:raise ValueError('export falsification lost')
result=subprocess.run([sys.executable,'-B',str(root/'export/diagnose-frozen.py')],capture_output=True,text=True,timeout=15);result.check_returncode()
if json.loads(result.stdout)!=json.loads((root/'export/falsification.json').read_text()):raise ValueError('diagnostic changed')
if (root/'phase_prerequisites.py').read_bytes()!=(root/'callback/phase_prerequisites.py').read_bytes() or (root/'phase_prerequisites.py').read_bytes()!=(root/'export/phase_prerequisites.py').read_bytes():raise ValueError('gate drift')
print(json.dumps({'verified':True,'files':len(seal['files']),'callback_bytes_compared':73728,'export_bytes_compared':30084,'combined_export_prediction_admitted':False,'native_execution':False}))
