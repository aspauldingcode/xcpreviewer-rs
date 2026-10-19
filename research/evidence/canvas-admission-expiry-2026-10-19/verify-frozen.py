from pathlib import Path
import hashlib,json,subprocess,sys,datetime
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
s=json.loads((p/'seal.json').read_text());need({f.name for f in p.iterdir() if f.name!='seal.json'}==set(s['files']),'closed file set')
for n,h in s['files'].items():need((p/n).is_file() and not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin '+n)
from sample_accounting import check
e=json.loads((p/'experiment.json').read_text());o=json.loads((p/'operation.json').read_text());c=json.loads((p/'cleanup-reconciliation.json').read_text());a=json.loads((p/'admission-observation.json').read_text());opening=json.loads((p/'opening-observation.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior'];history=json.loads((p/'readiness-observation.json').read_text())
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==e['source_sha256']==c['source_sha256']==a['source_sha256'],'source')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source')
need((p/'fixture-before.swift').read_text().replace(prior['nonce'],e['nonce'])==(p/'fixture-source.swift').read_text(),'nonce-only delta')
need(a['new_nonce']==e['nonce'] and a['old_nonce']==prior['nonce'] and a['retained_registry'] is True and a['old_nonce_error']=='session already bound' and a['new_nonce_error_separate_call']=='session already bound' and a['retired_app_error']=='retired holder' and a['AX_calls_during_admission']==0,'admission')
need(opening['owned_workspace_open_observed'] is True and opening['open_attempts']==1 and opening['clickCount']==2,'opening')
need(o['experiment_failed'] is True and o['original_deadline_met'] is False and o['deadline_extended'] is False and o['native_retry'] is False and o['second_session'] is False,'failure contract')
need(o['history']==history['history'] and check(o['history'])['count']==3 and history['outcomes']==['busy','ready','ready'] and history['fourth_sample_executed'] is False,'partial observations')
for k,w in [('holder_AX_observations',5),('cleanup_AX_observations',2),('total_AX_observations',7),('readiness_samples',3),('unused_samples',1),('refresh_clicks',0),('preview_selection_clicks',0),('receipt_observations',0),('CUA_inventory_calls',0),('getApp_calls',0),('host_app_launches',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0)]:need(type(o[k]) is int and o[k]==w,k)
need(o['callback_baseline_qualified'] is False and not(p/'assessment.json').exists() and not(p/'receipt-observation.json').exists(),'unexercised baseline')
parse=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
need(parse(e['stop_new_actions_utc'])<parse(e['deadline_utc'])<parse(o['holder_closed_at'])<=parse(o['workspace_closed_at'])<=parse(c['at']),'late reconciliation')
need(c['original_deadline_met'] is False and c['cleanup_only'] is True and type(c['owned_workspace_windows']) is int and c['owned_workspace_windows']==0 and c['broker_message']=='No workspace windows found','late zero')
for n,count in [('test-handoff.mjs',20),('test-owned-opener.mjs',12),('test-selection-only.mjs',13),('test-selection-registry.mjs',11),('test-session-driver.mjs',6)]:
 v=json.loads(subprocess.run(['node',str(p/n)],check=True,capture_output=True,text=True,timeout=10).stdout);need(type(v['cases']) is int and v['cases']==count and v['native_execution'] is False,n)
subprocess.run(['node',str(p/'test-admission-literal.mjs')],check=True,capture_output=True,timeout=10)
for opt in [[],['-O']]:
 for n in ['test_sample_accounting.py','test_decoder.py','test_exposure.py']:subprocess.run([sys.executable,*opt,'-B',str(p/n)],check=True,capture_output=True,timeout=10)
v=json.loads(json.loads((p/'graph-loop-inspection.json').read_text())['stdout']);need(v['execution_started'] is False and not v['candidates'],'graph')
v=json.loads(json.loads((p/'workgraph-inspection.json').read_text())['stdout']);need(v['milestone1_complete'] is False and v['milestone2_complete'] is False,'milestones')
print(json.dumps({'evidence_verified':True,'files':len(s['files']),'native_experiment_passed':False,'cleanup_deadline_met':False,'late_cleanup_reconciled':True,'actual_samples':3,'baseline_qualified':False}))
