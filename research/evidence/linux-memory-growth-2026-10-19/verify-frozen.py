"""Python-only frozen verification; never starts Docker or imports Wasmtime."""
from pathlib import Path
import json,subprocess,sys
from phase_prerequisites import parsed,require as need
import admit as a
from admit_recorded import observed
p=Path(__file__).resolve().parent;seal=parsed((p/'seal.json').read_text())
files={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.name!='seal.json' and '__pycache__' not in f.parts}
need(files==set(seal['files']),'complete inventory')
for n,h in seal['files'].items():
 f=p/n;need(not f.is_symlink() and f.resolve().is_relative_to(p) and a.H(f.read_bytes())==h,'sealed member')
for name,count in [('test_admission.py',4),('test_recorded.py',4),('admit.py',0),('admit_recorded.py',0)]:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,text=True,timeout=15);saved=parsed((p/(name+'.'+label+'.json')).read_text());need(z.returncode==saved['exit']==0,'verification exit')
  if count:need(('Ran %d tests'%count) in z.stderr and 'OK' in z.stderr and 'OK' in saved['stderr'],'fault controls')
  else:need(parsed(z.stdout)==parsed(saved['stdout']),'saved comparison')
v=observed(p);need(v['independent_bytes_compared']==524288 and v['producer_relation_bytes']==524288 and v['owned_cleanup_verified'] is True and v['existing_containers_preserved'] is True and v['js_host_view_semantics_measured'] is False and v['canvas_qualified'] is False,'scope')
need(parsed((p/'retained-inspection-type-failure.json').read_text())['original_reader_accepted'] is True,'retained counterexample')
print(json.dumps(v,sort_keys=True))
