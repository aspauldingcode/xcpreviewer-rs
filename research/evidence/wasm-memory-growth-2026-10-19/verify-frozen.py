"""Python-only frozen replay: never invokes Node or instantiates WASM."""
from pathlib import Path
import json
import subprocess
import sys
import build
from phase_prerequisites import parsed,require as need
import admit as a
p=Path(__file__).resolve().parent
seal=parsed((p/'seal.json').read_text())
files={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.name!='seal.json' and '__pycache__' not in f.parts}
need(files==set(seal['files']),'complete sealed inventory')
for n,h in seal['files'].items():
 f=p/n;need(not f.is_symlink() and f.resolve().is_relative_to(p) and a.H(f.read_bytes())==h,'sealed member')
need(build.module()==(p/'probe.wasm').read_bytes(),'module rebuild')
for name,count in [('test_admission.py',4),('test_recorded.py',3),('admit.py',0)]:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,text=True,timeout=15);saved=parsed((p/(name+'.'+label+'.json')).read_text())
  need(z.returncode==saved['exit']==0,'verification exit')
  if count:need(('Ran %d tests'%count) in z.stderr and 'OK' in z.stderr and 'OK' in saved['stderr'],'fault controls')
  else:need(parsed(z.stdout)==parsed(saved['stdout']),'complete result replay')
v=a.admit(p);need(v['all_bytes_compared']==524288 and v['zero_growth_detaches'] is True and v['failed_growth_preserves_buffer'] is True and v['canvas_qualified'] is False,'scope')
print(json.dumps(v,sort_keys=True))
