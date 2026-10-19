from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent
need=lambda value,message: None if value else (_ for _ in ()).throw(ValueError(message))
s=json.loads((p/'seal.json').read_text())
actual={x.name for x in p.iterdir() if x.name!='seal.json'}
need(actual==set(s['files']),'closed file set')
for n,h in s['files'].items():
 f=p/n;need(f.is_file() and not f.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==h,n)
for n,count in [('test-selection-only.mjs',13),('test-selection-registry.mjs',11),('test-session-driver.mjs',6)]:
 x=subprocess.run(['node',str(p/n)],check=True,capture_output=True,text=True,timeout=10);v=json.loads(x.stdout);need(type(v['cases']) is int and v['cases']==count and v['native_execution'] is False,n)
x=subprocess.run(['node',str(p/'test-binding-counterexample.mjs')],check=True,capture_output=True,text=True,timeout=10);v=json.loads(x.stdout);need(v['pre_fix_mismatch_dispatch_reproduced'] is True and v['post_fix_mismatch_rejected'] is True,'counterexample')
m=json.loads((p/'mutations.json').read_text());need(len(m)==5 and all(v['syntax_valid'] is True and v['rejected'] is True and v['returncode']!=0 for v in m),'retained mutations')
e=json.loads((p/'experiment.json').read_text());need(e['native_execution'] is False and e['native_experiment_calls']==0 and e['future_native_authorized_by_this_bundle'] is False,'scope')
for n in ['graph-loop','workgraph']:
 v=json.loads((p/(n+'-inspection.json')).read_text());need(v['returncode']==0 and v['execution_requested'] is False,n)
v=json.loads(json.loads((p/'graph-loop-inspection.json').read_text())['stdout']);need(v['execution_started'] is False and not v['candidates'] and v['all_milestones_complete'] is False,'graph loop')
v=json.loads(json.loads((p/'workgraph-inspection.json').read_text())['stdout']);need(v['milestone1_complete'] is False and v['milestone2_complete'] is False,'milestones')
subprocess.run([sys.executable,'-B',str(p/'mutate-controls.py'),'--verify'],check=True,capture_output=True,timeout=20)
print(json.dumps({'verified':True,'files':len(s['files']),'selection_cases':13,'registry_cases':11,'driver_cases':6,'mutants_retained':5,'native_execution':False}))
