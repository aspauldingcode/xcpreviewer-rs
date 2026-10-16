import ast,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');out=Path('/private/tmp/r1-partial-typed-20261016');out.mkdir(exist_ok=False)
old=(r/'tools/re/tests/verify_surface_partial_right.py').read_text();(out/'original-verifier.py').write_text(old)
fields=['pid','send_code','invalid_right_constant','original_name','returned_name','second_name','first_disposition','second_disposition','remote_type','before_original','before_returned','before_endpoint','after_original','after_returned','after_endpoint','invalid_type_before','invalid_query_after','invalid_type_after','empty_receive_code','remaining_send_refs','stride','allocation_bytes']
new=old.replace("_require(json.loads((e / 'compile-wait.json').read_text()) == {'code': 0})", "_require(type(json.loads((e / 'compile-wait.json').read_text())['code']) is int)\n    _require(json.loads((e / 'compile-wait.json').read_text()) == {'code': 0})")
new=new.replace("_require(json.loads((root / 'wait.json').read_text()) == {'code': 0, 'timeout': False})", "_require(type(json.loads((root / 'wait.json').read_text())['code']) is int and json.loads((root / 'wait.json').read_text())['timeout'] is False)\n        _require(json.loads((root / 'wait.json').read_text()) == {'code': 0, 'timeout': False})")
new=new.replace("r = rows[0]", "r = rows[0]\n        _require(all(type(r[key]) is int for key in "+repr(fields)+"))");(out/'repaired-verifier.py').write_text(new)
def preds(s):return [ast.dump(n.args[0],include_attributes=False) for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require']
a=preds(old);b=iter(preds(new));assert all(any(v==x for v in b) for x in a)
(out/'predicate-preservation.json').write_text(json.dumps({'prior_require_predicates':len(a),'prior_predicates_preserved_in_order':True,'new_predicates':3,'numeric_row_fields':fields},indent=2)+'\n')
e=r/'research/evidence/surface-partial-cleanup-2026-10-14';h=hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest();assert h=='d8c5acef6c6154e836c639869591d0e18d226576cc7bcbf9b9cf6ce6488f1d76';m=json.loads((e/'manifest.json').read_text());assert all((e/n).stat().st_size==v['bytes'] and hashlib.sha256((e/n).read_bytes()).hexdigest()==v['sha256'] for n,v in m['files'].items())
rows=[];faults=['positive','pid_float','returned_name_float','second_name_float','endpoint_bool','remaining_refs_bool','compile_code_bool','wait_code_bool','timeout_int','send_code_float','stride_float']
for label,path in [('original',out/'original-verifier.py'),('repaired',out/'repaired-verifier.py')]:
 for optimized in [False,True]:
  for fault in faults:
   with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)/'e';shutil.copytree(e,d);p=d/'move/stdout.jsonl';v=json.loads(p.read_text())
    if fault in ['pid_float','returned_name_float','second_name_float','send_code_float','stride_float']:
     key=fault[:-6];v[key]=float(v[key]);p.write_text(json.dumps(v)+'\n')
    elif fault=='endpoint_bool':v['after_endpoint']=True;p.write_text(json.dumps(v)+'\n')
    elif fault=='remaining_refs_bool':v['remaining_send_refs']=False;p.write_text(json.dumps(v)+'\n')
    elif fault=='compile_code_bool':(d/'compile-wait.json').write_text(json.dumps({'code':False}))
    elif fault=='wait_code_bool':(d/'move/wait.json').write_text(json.dumps({'code':False,'timeout':False}))
    elif fault=='timeout_int':(d/'move/wait.json').write_text(json.dumps({'code':0,'timeout':0}))
    (d/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(d)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in d.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    script="import importlib.util,json;s=importlib.util.spec_from_file_location('v',"+repr(str(path))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.verify("+repr(str(d))+")))"
    q=subprocess.run([sys.executable,*(['-O'] if optimized else []),'-c',script],capture_output=True,text=True,timeout=10);rows.append({'verifier':label,'optimized':optimized,'fault':fault,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr});assert (q.returncode==0)==(fault=='positive' or label=='original')
(out/'frozen-experiment.json').write_text(json.dumps({'historical_manifest_sha256':h,'historical_files_verified':len(m['files']),'rows':rows},indent=2)+'\n');print(json.dumps({'runs':len(rows),'false_acceptances_per_original_mode':len(faults)-1,'fields':len(fields)}))
