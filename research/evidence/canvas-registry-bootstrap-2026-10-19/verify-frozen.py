from pathlib import Path
import json,hashlib,datetime,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin '+n)
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());selection=json.loads((p/'selection.json').read_text());probe=json.loads((p/'bootstrap-probes.json').read_text())
for k in ['workspace_opens','AX_observations','readiness_samples','refresh_clicks','preview_selection_clicks','CUA_inventory_calls','getApp_calls','host_app_selections','host_app_launches','increment_clicks','coordinate_clicks','renderpreview_calls','receipt_observations']:need(type(op[k]) is int and op[k]==0,k)
need(op['baseline_qualified'] is False and op['live_host_inventory_measured'] is False and op['native_retry'] is False and op['bootstrap_proposal_used_for_native_UI'] is False,'native scope')
need(probe['native_admission_failure']['error']==op['error']=='ownedRegistry is not defined' and probe['native_admission_failure']['before_any_UI_call'] is True,'failure')
need(probe['context_diagnostic']['ownedRegistry']=='undefined' and all(probe['context_diagnostic'][x]=='function' for x in ['createSessionRegistry','createReadiness','assess','normalize','guardedClick']),'context limits')
need(probe['conditional_var']['same_call']['nested']=='object' and probe['conditional_var']['next_call']['nested']=='undefined' and probe['conditional_var']['next_call']['top']=='object','declaration witness')
need(probe['top_level_self_initializer_repeated']['duplicate_binding_rejected'] is False and probe['top_level_self_initializer_repeated']['second_call_error']=='registry was reset','rejected alternative')
need(probe['strict_hasOwn_property_initializer']['next_call_duplicate_rejected'] is True and probe['strict_hasOwn_property_initializer']['UI_calls']==0,'pure strict control')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'prepared source')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==selection['prior']['source_sha256'],'prior source')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('24e447b779314b648597edd1dfea717e',plan['nonce']),'nonce-only preparation')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','zero windows')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
need(parse(cleanup['at'])<parse(plan['deadline_utc']),'closed before deadline')
for opt in [[],['-O']]:
 for name in ['test_readiness_schedule.py','test_normalize_selected.py','test_exposure.py','test_decoder.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],check=True,capture_output=True,timeout=10)
for name in ['test-bootstrap.mjs','test-local-readiness.mjs','test-session-registry.mjs','test-action.mjs','test-normalized-guard.mjs','test-guard.mjs']:subprocess.run(['node',str(p/name)],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'native_UI_calls':0,'inventory_calls':0,'caller_admission_failed':True,'pure_property_control_duplicate_rejected':True,'bootstrap_VM_cases':7,'corrected_bootstrap_used_for_native_UI':False,'cleanup_verified':True}))
