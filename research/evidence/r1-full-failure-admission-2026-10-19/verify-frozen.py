"""Read-only counterexample replay; native processes are never launched."""
from pathlib import Path
import json,hashlib,ast,subprocess,sys
p=Path(__file__).resolve().parent
need=lambda c: None if c else (_ for _ in ()).throw(ValueError('R1 full-failure evidence rejected'))
def h(q):return hashlib.sha256(q.read_bytes()).hexdigest()
s=json.loads((p/'seal.json').read_text());files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts};need(files==set(s['files']))
for n,d in s['files'].items():need(not (p/n).is_symlink() and h(p/n)==d)
a=Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-full-failure-2026-10-11');need(h(a/'manifest.json')=='e6d6c1cb5bac06343c547dcfe0b633908b43ef900b511c8a2c03d9b85f332a72')
for n,x in json.loads((a/'manifest.json').read_text())['files'].items():need((a/n).stat().st_size==x['bytes'] and h(a/n)==x['sha256'])
before=ast.parse((p/'before.py').read_text());after=ast.parse((p/'after.py').read_text());pred=[ast.dump(x.test,include_attributes=False) for x in ast.walk(before) if isinstance(x,ast.Assert)];calls=[ast.dump(x.args[0],include_attributes=False) for x in ast.walk(after) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_require' and x.args];need(len(pred)==14 and all(x in calls for x in pred) and not any(isinstance(x,ast.Assert) for x in ast.walk(after)))
summary={}
for source in ['before','after']:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/'audit.py'),source],capture_output=True,text=True,timeout=20);need(z.returncode==0);actual=json.loads(z.stdout);saved=json.loads((p/(source+'.'+label+'.json')).read_text());need(saved['exit']==0 and saved['stderr']=='' and actual==json.loads(saved['stdout']))
  invalid=[x for x in actual['cases'] if x['fault']!='positive' and x['accepted']];need(actual['cases'][0]['fault']=='positive' and actual['cases'][0]['accepted'] is True)
  need(len(invalid)==(17 if label=='normal' else 29) if source=='before' else len(invalid)==0);summary[source+'_'+label+'_invalid_accepted']=len(invalid)
for label in ['normal','optimized']:
 v=json.loads((p/('integrated-tests.'+label+'.json')).read_text());need(v['exit']==0 and 'OK' in v['stderr'])
print(json.dumps({'matrix':summary,'original_predicates_preserved':14,'historical_bytes_verified':65536,'native_execution':False,'physical_reclamation':False,'canvas_qualified':False}))
