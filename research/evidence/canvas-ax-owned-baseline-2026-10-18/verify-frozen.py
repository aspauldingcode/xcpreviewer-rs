from pathlib import Path
import json,hashlib,datetime,subprocess,sys
from decoder import record
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'pin '+n)
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());s=json.loads((p/'local-sampler-observation.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior'];assessment=json.loads((p/'assessment.json').read_text());obs=json.loads((p/'receipt-observation.json').read_text());build=json.loads((p/'build-association.json').read_text());ax=json.loads((p/'ax-exposure-observation.json').read_text())
for k,w in [('workspace_opens',1),('refresh_clicks',0),('preview_selection_clicks',1),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('AX_observations',9),('passive_readiness_observations',2),('receipt_observations',1)]:need(type(op[k]) is int and op[k]==w,k)
need(op['AX_observations']<=plan['maximum_state_observations'] and op['passive_readiness_observations']<=plan['maximum_passive_readiness_observations'],'observation budgets')
need(s['failed'] is False and s['pending'] is False and s['registry_instances_created']==s['nonce_bindings']==1 and len(s['history'])==2,'one bounded sampler')
need(s['history'][0]>=15 and s['history'][1]>=max(45,s['history'][0]+30),'spacing')
need(s['session']==s['context']['session']==plan['nonce'] and s['context']['workspace']==plan['workspace'] and s['context']['source_sha256']==plan['source_sha256'],'lease context')
need(s['early_call_returned_independent_work'] is True and abs(s['early_call_not_before_wall']-(s['start']['wall']+s['history'][0]+30))<0.001,'no early observation refill')
need(op['matching_nonbusy_signatures'] is True and op['previous_signature_length']==op['fresh_signature_length']==7221,'recorded guard equality')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source hash')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('8427ed5dcb094e7eb2a62bc4d0ae7332',plan['nonce']),'nonce-only delta')
expected_binary='/Users/8amps/Library/Developer/Xcode/DerivedData/PreviewLab-aybvehbjrqcwptcgpubkgsryjlxa/Build/Products/Debug/PreviewLab.app/Contents/MacOS/PreviewLab'
need(build['binary_path']==expected_binary and build['filelist_utf8']=='/tmp/callback-ui-access-20261018/workspace/Sources/PreviewLab/PreviewLab.swift\n','exact owned build source association')
need(hashlib.sha256(build['filelist_utf8'].encode()).hexdigest()==build['filelist_sha256'],'filelist bytes')
need(len(obs['records'])==1,'one baseline receipt');x=obs['records'][0];live=x['live_identity'];identity=assessment['identity']
need(type(live['pid']) is int and live['pid']==identity['pid']==76585 and live['state']=='L' and live['identity']==[1792364725,325211,expected_binary],'live identity')
need(identity['nonce']==plan['nonce'] and identity['view']==op['visual']['view']=='96a040cf-c557-4ebd-846c-a00e3b4de71e' and op['visual']['count']==0,'visual/nonce binding')
raw=bytes.fromhex(x['raw_hex']);record(raw,x['name'],identity,'appear',0,0);need(raw==(p/'native-receipt.json').read_bytes() and len(raw)==assessment['bytes_compared']==154,'all receipt bytes')
need(assessment['baseline_qualified'] is True and assessment['input_qualified'] is False and assessment['private_transport_proven'] is False and assessment['general_sandbox_policy_proven'] is False,'scope')
need(ax['ownership_assessed'] is True and ax['node_count']==129 and ax['signature_length']==7221 and ax['source_editor_subtrees_excluded'] is True and ax['candidate_indices']=={'owned.callback.root':[],'owned.callback.count':[],'owned.callback.increment':[]} and ax['native_action_authorized'] is False,'recorded bounded AX observation')
need(op['summary_boundary_native_verified'] is False and op['native_selected_summary_encountered'] is False,'summary branch scope')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','cleanup')
need(parse(cleanup['at'])<parse(plan['deadline_utc']) and parse(op['closed_by'])<parse(plan['deadline_utc']) and parse(op['selection_completed_by'])<parse(plan['stop_new_actions_utc']),'cutoffs')
need(s['stopWall']==parse(plan['stop_new_actions_utc']).timestamp() and s['cleanupWall']==parse(plan['deadline_utc']).timestamp(),'fixed gate cutoffs')
for opt in [[],['-O']]:
 for name in ['test_readiness_schedule.py','test_normalize_selected.py','test_exposure.py','test_decoder.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],check=True,capture_output=True,timeout=10)
for name in ['test-guard.mjs','test-normalized-guard.mjs','test-action.mjs','test-local-readiness.mjs','test-session-registry.mjs']:subprocess.run(['node',str(p/name)],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'native_readiness_samples':2,'native_title_selection':1,'baseline_bytes':154,'scoped_AX_identifier_candidates':0,'input_qualified':False,'raw_AX_retained':False,'cleanup_verified':True}))
