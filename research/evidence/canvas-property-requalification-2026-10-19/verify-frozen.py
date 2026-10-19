from pathlib import Path
import json,hashlib,datetime,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin '+n)
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior'];reg=json.loads((p/'registry-observation.json').read_text())
for k,w in [('workspace_opens',1),('AX_observations',7),('readiness_samples',2),('refresh_action_wrapper_attempts',1),('refresh_clicks',0),('preview_selection_clicks',0),('CUA_inventory_calls',0),('getApp_calls',0),('host_app_selections',0),('host_app_launches',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('receipt_observations',0)]:need(type(op[k]) is int and op[k]==w,k)
need(op['error']=='busy' and op['matching_action_pair_qualified'] is False and op['fresh_signature_length'] is None and op['callback_baseline_qualified'] is False and op['live_host_inventory_measured'] is False and op['native_retry'] is False,'failure scope')
need(op['actual_nonce_cross_call_duplicate_rejected'] is True and op['strict_property_bootstrap_native_used'] is True and op['session_driver_proposal_native_used'] is False,'integration scope')
need(reg['production_property_absent_at_preflight'] is True and reg['property_initialized_once'] is True and reg['same_actual_nonce_duplicate_rejected_in_separate_call_before_UI'] is True,'recorded lifetime gate')
need(reg['context']['session']==reg['session']==plan['nonce'] and reg['context']['workspace']==plan['workspace'] and reg['context']['source_sha256']==plan['source_sha256'],'context')
need(len(reg['history'])==2 and reg['history'][0]>=15 and reg['history'][1]>=max(45,reg['history'][0]+30) and reg['failed'] is False and op['sampler_failed_flag'] is False,'passive sampler scope')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source hash')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('c2418f5ffd644b9fa598c00d12425958',plan['nonce']),'nonce-only delta')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','zero windows')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
need(parse(cleanup['at'])<parse(plan['deadline_utc']) and parse(op['closed_by'])<parse(plan['deadline_utc']),'deadline')
need(reg['stopWall']==parse(plan['stop_new_actions_utc']).timestamp() and reg['cleanupWall']==parse(plan['deadline_utc']).timestamp(),'fixed cutoffs')
for opt in [[],['-O']]:
 for n in ['test_readiness_schedule.py','test_normalize_selected.py','test_exposure.py','test_decoder.py']:subprocess.run([sys.executable,*opt,'-B',str(p/n)],check=True,capture_output=True,timeout=10)
for n in ['test-session-driver.mjs','test-bootstrap.mjs','test-local-readiness.mjs','test-session-registry.mjs','test-action.mjs','test-normalized-guard.mjs','test-guard.mjs']:subprocess.run(['node',str(p/n)],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'actual_registry_duplicate_rejected':True,'native_refresh_dispatched':0,'native_action_requalification_failed':True,'inventory_measured':False,'session_driver_cases':6,'session_driver_native_used':False,'cleanup_verified':True}))
