from pathlib import Path
import hashlib,json,datetime,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin '+n)
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior']
for k,want in [('workspace_opens',1),('refresh_clicks',1),('preview_selection_clicks',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('AX_observations',12),('passive_readiness_observations',4),('receipt_observations',0)]:need(type(op[k]) is int and op[k]==want,k)
need(op['AX_observations']<=plan['maximum_state_observations'] and op['passive_readiness_observations']==plan['maximum_passive_readiness_observations'],'budget')
need(op['outcome']=='readiness_observation_cap_exhausted' and op['callback_view_rendered'] is False and op['AX_exposure_qualified'] is False,'failure scope')
need(op['native_Selected_summary_encountered'] is False and op['summary_boundary_native_verified'] is False and op['normalized_guard_used_for_native_Refresh'] is True,'native adapter scope')
need(op['matching_nonbusy_refresh_signatures'] is True and op['previous_refresh_signature_length']==op['fresh_refresh_signature_length']==6697,'recorded signature equality')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source hash')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source hash')
old='2d55a70fe57a4603ad5b98a852a1b413';need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace(old,plan['nonce']),'nonce-only delta')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','zero windows')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
need(parse(cleanup['at'])<parse(plan['deadline_utc']) and parse(op['closed_by'])<parse(plan['deadline_utc']) and parse(op['refresh_completed_by'])<parse(plan['stop_new_actions_utc']),'deadline')
for opt in [[],['-O']]:
 for name in ['test_normalize_selected.py','test_exposure.py','test_readiness_schedule.py','test_decoder.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],check=True,capture_output=True,timeout=10)
for name in ['test-guard.mjs','test-normalized-guard.mjs','test-action.mjs']:subprocess.run(['node',str(p/name)],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'native_refresh_actions':1,'native_title_selection_actions':0,'native_readiness_cap_exhausted':True,'cleanup_verified':True,'AX_exposure_qualified':False,'spaced_scheduler_native_used':False}))
