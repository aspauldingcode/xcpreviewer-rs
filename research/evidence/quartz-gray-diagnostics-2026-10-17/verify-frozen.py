import hashlib,json,subprocess,sys,struct,math
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=json.loads((p/'seal.json').read_text())
for name,h in s['files'].items():
 f=p/name
 if f.is_symlink() or sha(f)!=h:raise ValueError('Seal mismatch: '+name)
for kind in ['boundary','half']:
 code="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from admit import admitted;print(json.dumps(admitted(Path(sys.argv[1]))))"
 x=subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),'-B','-c',code,str(p/kind)],capture_output=True,text=True,timeout=10)
 if x.returncode:raise ValueError(x.stderr)
 if json.loads(x.stdout)!=json.loads((p/kind/'admission.json').read_text()):raise ValueError('Admission changed')
for phase in range(3):
 for label,path in [('quartz',p/'boundary/owned-documents'/('phase%d-route1.raw'%phase)),('callback',p/'boundary/references'/('callback-phase%d.raw'%phase))]:
  if (p/'half/references'/('%s-phase%d.raw'%(label,phase))).read_bytes()!=path.read_bytes():raise ValueError('Reference provenance changed')
for v,bits in [(.25,14412),(.5,14818)]:
 encoded=12.92*v if v<=.0031308 else 1.055*math.pow(v,1/2.4)-.055
 if struct.unpack('<H',struct.pack('<e',encoded))[0]!=bits:raise ValueError('IEEE-half independent prediction')
print(json.dumps({'files_verified':len(s['files']),'full_bytes_compared':73728,'native_launched':False,'internal_renderer_precision_proven':False}))
