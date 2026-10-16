import ast,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');out=Path('/private/tmp/r1-partial-optimized-20261016');out.mkdir(exist_ok=False)
source=r/'tools/re/tests/verify_surface_partial_right.py';old=source.read_text();(out/'original-verifier.py').write_text(old)
tree=ast.parse(old);predicates=[ast.dump(n.test,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Assert)]
class Change(ast.NodeTransformer):
 def visit_Assert(self,node):return ast.copy_location(ast.Expr(value=ast.Call(func=ast.Name(id='_require',ctx=ast.Load()),args=[node.test],keywords=[])),node)
new=ast.unparse(ast.fix_missing_locations(Change().visit(tree)))+'\n';new="def _require(condition):\n    if not condition:\n        raise AssertionError('Partial-right evidence admission rejected')\n\n"+new;(out/'repaired-verifier.py').write_text(new)
actual=[ast.dump(n.args[0],include_attributes=False) for n in ast.walk(ast.parse(new)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require'];assert predicates==actual
(out/'predicate-preservation.json').write_text(json.dumps({'assertions_replaced':len(predicates),'predicate_ASTs_equal':True},indent=2)+'\n')
e=r/'research/evidence/surface-partial-cleanup-2026-10-14';expected='d8c5acef6c6154e836c639869591d0e18d226576cc7bcbf9b9cf6ce6488f1d76';assert hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest()==expected
m=json.loads((e/'manifest.json').read_text());assert all((e/n).stat().st_size==v['bytes'] and hashlib.sha256((e/n).read_bytes()).hexdigest()==v['sha256'] for n,v in m['files'].items())
rows=[]
for label,path in [('original',out/'original-verifier.py'),('repaired',out/'repaired-verifier.py')]:
 for opt in [False,True]:
  for fault in ['positive','wait_code','endpoint_refs','padding','tail']:
   with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)/'e';shutil.copytree(e,d)
    if fault=='wait_code':(d/'move/wait.json').write_text(json.dumps({'code':7,'timeout':False}))
    elif fault=='endpoint_refs':
     f=d/'move/stdout.jsonl';v=json.loads(f.read_text());v['after_endpoint']=2;f.write_text(json.dumps(v)+'\n')
    elif fault in ['padding','tail']:
     f=d/'move/alias-after-cleanup.bin';v=bytearray(f.read_bytes());v[68 if fault=='padding' else 16383]^=1;f.write_bytes(v)
    (d/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(d)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in d.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    script="import importlib.util,json; s=importlib.util.spec_from_file_location('v',"+repr(str(path))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.verify("+repr(str(d))+")))"
    q=subprocess.run([sys.executable,*(['-O'] if opt else []),'-c',script],capture_output=True,text=True,timeout=10);rows.append({'verifier':label,'optimized':opt,'fault':fault,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
    should_accept=fault=='positive' or(label=='original' and opt);assert (q.returncode==0)==should_accept
(out/'frozen-experiment.json').write_text(json.dumps({'historical_manifest_sha256':expected,'historical_files_verified':len(m['files']),'rows':rows},indent=2)+'\n');print(json.dumps({'assertions':len(predicates),'rows':len(rows),'original_optimized_false_acceptances':4,'repaired_rejects_all':True}))
