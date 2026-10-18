from pathlib import Path
import json,hashlib,datetime,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'pin '+n)
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());s=json.loads((p/'sample-schedule.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior']
for k,w in [('workspace_opens',1),('refresh_clicks',0),('preview_selection_clicks',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('AX_observations',4),('passive_readiness_observations',0),('readiness_permits_issued',1),('receipt_observations',0)]:need(type(op[k]) is int and op[k]==w,k)
need(op['failed_guard_invoked_AX'] is False and op['actual_failed_call_age_seconds'] is None and op['outcome']=='permit_age_guard_rejected_before_AX','failure scope')
need(op['callback_view_rendered'] is False and op['AX_exposure_qualified'] is False and op['native_retry'] is False and op['local_readiness_proposal_native_used'] is False,'claim limits')
need(s['failed'] is True and s['pending'] is None and len(s['records'])==len(s['history'])==1,'terminal lease error')
x=s['records'][0];need(x['issue']['ordinal']==1 and x['issue']['issued_wall']==op['issued_wall'] and x['issue']['issued_elapsed']>=15 and x['completion']['outcome']=='error','permit')
need(s['history'][0]==x['completion']['elapsed'] and x['completion']['elapsed']>=x['issue']['issued_elapsed'],'completion')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('7be0f730232c46099a3c5e6feecc2728',plan['nonce']),'nonce-only delta')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','cleanup')
need(parse(cleanup['at'])<parse(plan['deadline_utc']) and parse(op['closed_by'])<parse(plan['deadline_utc']),'cleanup cutoff')
need(abs((s['start_wall']+s['stop_elapsed'])-parse(plan['stop_new_actions_utc']).timestamp())<0.001,'fixed stop')
for opt in [[],['-O']]:
 for name in ['test_sampler.py','test_readiness_schedule.py','test_normalize_selected.py','test_exposure.py','test_decoder.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],check=True,capture_output=True,timeout=10)
for name in ['test-guard.mjs','test-normalized-guard.mjs','test-action.mjs','test-local-readiness.mjs']:subprocess.run(['node',str(p/name)],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'native_permits':1,'native_readiness_AX_calls':0,'terminal_error':True,'cleanup_verified':True,'local_proposal_cases':10,'local_proposal_native_used':False}))
