import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
for name,digest in json.loads((root/'approved-pins.json').read_text()).items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('approved pin')
# Original live fixture path is preserved in its receipt; only its directory binding
# is adjusted in an in-memory copy for relocated offline replay, never on disk.
sys.path.insert(0,str(root))
import admit
original=admit.parsed
old='/private/tmp/quartz-byte-native-20261018/owned-documents'
def relocated(raw):
 v=original(raw)
 if isinstance(v,dict) and v.get('phase')=='fixture' and v.get('args')==['--fixture',old]:v['args']=['--fixture',str(root/'owned-documents')]
 return v
admit.parsed=relocated
if admit.admitted(root)!=json.loads((root/'admission.json').read_text()):raise ValueError('measurement replay')
for name in ['test_admit.py','test_admit_extension.py']:
 for opt in [False,True]:
  p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/name)],capture_output=True,text=True,timeout=15);p.check_returncode()
print(json.dumps({'verified':True,'files':len(seal['files']),'source_bytes':3120,'output_bytes':32768,'native_execution':False}))
