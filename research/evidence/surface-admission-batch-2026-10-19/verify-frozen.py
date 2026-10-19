"""Frozen grouped CPU admission replay; no native fixture execution."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs')
def need(condition):
 if not condition:raise ValueError('Surface admission batch rejected')
def h(q):return hashlib.sha256(q.read_bytes()).hexdigest()
s=json.loads((p/'seal.json').read_text());files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts};need(files==set(s['files']))
for n,d in s['files'].items():need(not (p/n).is_symlink() and h(p/n)==d)
catalog=json.loads((p/'selection.json').read_text())['catalog'];need(len(catalog)==14);predicates=0
for x in catalog:
 a=r/x['evidence'];need(h(a/'manifest.json')==x['manifest_sha256'])
 for n,v in json.loads((a/'manifest.json').read_text())['files'].items():need((a/n).stat().st_size==v['bytes'] and h(a/n)==v['sha256'])
 before=ast.parse((p/'before'/x['reader']).read_text());after=ast.parse((p/'after'/x['reader']).read_text());old=[ast.dump(n.test,include_attributes=False) for n in ast.walk(before) if isinstance(n,ast.Assert)];new=[ast.dump(n.args[0],include_attributes=False) for n in ast.walk(after) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require' and n.args]
 need(old==new and len(old)==x['asserts'] and not any(isinstance(n,ast.Assert) for n in ast.walk(after)));predicates+=len(old)
need(predicates==247);counts={};byte_totals=[]
for source in ['before','after']:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/'audit.py'),source],capture_output=True,text=True,timeout=30);need(z.returncode==0);actual=json.loads(z.stdout);saved=json.loads((p/(source+'.'+label+'.json')).read_text());need(saved['exit']==0 and saved['stderr']=='' and actual==json.loads(saved['stdout']))
  results=actual['results'];need(sum(x['tests'] for x in results)==28)
  bad=[y for x in results for y in x['records'] if y.get('subtest_error')];accepted=[y for y in bad if y.get('message')=='AssertionError not raised'];fallthrough=[y for y in bad if y.get('exception')=='FileNotFoundError' and y.get('message','').startswith('missing fixture member: ')]
  old_optimized=source=='before' and label=='optimized';need(len(accepted)==(206 if old_optimized else 0) and len(fallthrough)==(6 if old_optimized else 0) and len(bad)==len(accepted)+len(fallthrough))
  need(sum(x['failures'] for x in results)==len(accepted) and sum(x['errors'] for x in results)==len(fallthrough));counts[source+'_'+label]={'accepted_faults':len(accepted),'file_error_fallthroughs':len(fallthrough)}
  byte_totals.append(sum(next(x['positive_result'][k] for k in ['complete_bytes','full_allocation_bytes','full_bytes_compared'] if k in x['positive_result']) for x in results))
need(byte_totals==[7077888]*4)
for label in ['normal','optimized']:
 v=json.loads((p/('integrated-tests.'+label+'.json')).read_text());need(v['exit']==0 and 'Ran 30 tests' in v['stderr'] and 'OK' in v['stderr'])
print(json.dumps({'readers':14,'predicates_preserved':247,'matrix':counts,'historical_complete_bytes':7077888,'native_execution':False,'canvas_qualified':False}))
