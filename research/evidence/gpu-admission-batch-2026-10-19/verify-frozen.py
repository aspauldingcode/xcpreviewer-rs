"""Frozen grouped admission replay; no native GPU/process fixture execution."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs')
def need(condition):
 if not condition:raise ValueError('GPU admission batch rejected')
def h(q):return hashlib.sha256(q.read_bytes()).hexdigest()
s=json.loads((p/'seal.json').read_text());files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts};need(files==set(s['files']))
for n,d in s['files'].items():need(not (p/n).is_symlink() and h(p/n)==d)
catalog=json.loads((p/'selection.json').read_text())['catalog'];need(len(catalog)==8);predicates=0
for x in catalog:
 a=r/x['evidence'];need(h(a/'manifest.json')==x['manifest_sha256'])
 for n,v in json.loads((a/'manifest.json').read_text())['files'].items():need((a/n).stat().st_size==v['bytes'] and h(a/n)==v['sha256'])
 before=ast.parse((p/'before'/x['reader']).read_text());after=ast.parse((p/'after'/x['reader']).read_text());old=[ast.dump(n.test,include_attributes=False) for n in ast.walk(before) if isinstance(n,ast.Assert)];new=[ast.dump(n.args[0],include_attributes=False) for n in ast.walk(after) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require' and n.args]
 need(old==new and len(old)==x['asserts'] and not any(isinstance(n,ast.Assert) for n in ast.walk(after)));predicates+=len(old)
need(predicates==178);counts={};byte_totals=[]
for source in ['before','after']:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/'audit.py'),source],capture_output=True,text=True,timeout=30);need(z.returncode==0);actual=json.loads(z.stdout);saved=json.loads((p/(source+'.'+label+'.json')).read_text());need(saved['exit']==0 and saved['stderr']=='' and actual==json.loads(saved['stdout']))
  results=actual['results'];need(sum(x['tests'] for x in results)==16 and sum(x['errors'] for x in results)==0)
  bad=[y for x in results for y in x['records'] if y.get('accepted_fault')];failures=sum(x['failures'] for x in results);expected=63 if source=='before' and label=='optimized' else 0
  need(failures==len(bad)==expected and all(y['message']=='AssertionError not raised' for y in bad));counts[source+'_'+label+'_accepted_faults']=failures
  byte_totals.append(sum(x['positive_result']['complete_bytes'] for x in results))
need(byte_totals==[1507328]*4)
for label in ['normal','optimized']:
 v=json.loads((p/('integrated-tests.'+label+'.json')).read_text());need(v['exit']==0 and 'Ran 18 tests' in v['stderr'] and 'OK' in v['stderr'])
print(json.dumps({'readers':8,'predicates_preserved':178,'matrix':counts,'historical_complete_bytes':1507328,'native_execution':False,'canvas_qualified':False}))
