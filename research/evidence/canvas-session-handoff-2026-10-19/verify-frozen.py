from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
s=json.loads((p/'seal.json').read_text());need({n.name for n in p.iterdir() if n.name!='seal.json'}==set(s['files']),'closed file set')
for n,h in s['files'].items():need((p/n).is_file() and not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'inherited-pins.json').read_text()).items():need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'inherited '+n)
v=json.loads((p/'experiment.json').read_text());need(v['native_experiment_started'] is False and v['native_handoff_integrated'] is False and v['CUA_calls']==0 and v['fixture_source_edited'] is False and v['next_native_plan_review_required'] is True,'scope')
v=json.loads((p/'selection.json').read_text());need(v['prior']['seal_sha256']=='2977d8d66a11677007a65a8036eaf8507253bcaa271d3063b21df823230cc095' and v['prior']['experiment_deadline_closed'] is True and v['prior']['cleanup_reconciliation_required'] is False and v['source_sha256']==v['prior']['source_sha256'],'prior')
for n,count in [('test-handoff.mjs',20),('test-owned-opener.mjs',12)]:
 x=subprocess.run(['node',str(p/n)],check=True,capture_output=True,text=True,timeout=10);v=json.loads(x.stdout);need(type(v['cases']) is int and v['cases']==count and v['native_execution'] is False,n)
x=subprocess.run(['node',str(p/'test-counterexamples.mjs')],check=True,capture_output=True,text=True,timeout=10);v=json.loads(x.stdout)
for key in ['initial_closed_reset_reproduced','initial_counter_reset_reproduced','corrected_rejects_both','pre_fix_late_click_success_reproduced','corrected_suppresses_late_click_result']:need(v[key] is True,key)
m=json.loads((p/'mutations.json').read_text());need(len(m)==5 and all(x['syntax_valid'] is True and x['rejected'] is True and x['returncode']!=0 for x in m),'mutants')
subprocess.run([sys.executable,'-B',str(p/'mutate-controls.py'),'--verify'],check=True,capture_output=True,timeout=20)
v=json.loads(json.loads((p/'graph-loop-inspection.json').read_text())['stdout']);need(v['execution_started'] is False and not v['candidates'],'graph loop')
v=json.loads(json.loads((p/'workgraph-inspection.json').read_text())['stdout']);need(v['milestone1_complete'] is False and v['milestone2_complete'] is False,'milestones')
print(json.dumps({'verified':True,'files':len(s['files']),'case_groups':20,'opener_cases':12,'mutants':5,'native_handoff_integrated':False}))
