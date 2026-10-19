"""Python-only verification; never compiles or evaluates an engine fixture."""
from pathlib import Path
import json,re,subprocess,sys
from phase_prerequisites import parsed,require as need
import admit as a
p=Path(__file__).resolve().parent;seal=parsed((p/'seal.json').read_text())
files={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.name!='seal.json' and '__pycache__' not in f.parts}
need(files==set(seal['files']),'complete inventory')
for n,h in seal['files'].items():
 f=p/n;need(not f.is_symlink() and f.resolve().is_relative_to(p) and a.b.H(f.read_bytes())==h,'sealed member')
raw=parsed(re.search(r'const bytes=new Uint8Array\((\[.*?\])\);',(p/'probe.js').read_text()).group(1));need(bytes(raw)==(p/'probe.wasm').read_bytes(),'embedded module')
for name,count in [('test_byte_compare.py',4),('test_acquire.py',4),('test_recorded.py',4),('admit.py',0)]:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,text=True,timeout=15);saved=parsed((p/(name+'.'+label+'.json')).read_text());need(z.returncode==saved['exit']==0,'verification exit')
  if count:need(('Ran %d tests'%count) in z.stderr and 'OK' in z.stderr and 'OK' in saved['stderr'],'fault controls')
  else:need(parsed(z.stdout)==parsed(saved['stdout']),'saved comparison')
v=a.observed(p);need(v['all_bytes_compared']==524288 and v['producer_relation_bytes']==524288 and v['second_engine_verified'] is True and v['browser_verified'] is False and v['non_Apple_OS_verified'] is False and v['canvas_qualified'] is False,'scope')
print(json.dumps(v,sort_keys=True))
