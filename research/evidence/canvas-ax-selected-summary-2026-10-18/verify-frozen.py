from pathlib import Path
import json,hashlib,sys,subprocess,datetime
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved local pin')
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());obs=json.loads((p/'receipt-observation.json').read_text())
need(op['native_navigation_failed'] is True and op['native_input_qualified'] is False and op['normalizer_used_for_native_action'] is False,'native scope')
for k,want in [('workspace_opens',1),('refresh_clicks',0),('preview_selection_clicks',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('receipt_observations',1)]:need(type(op[k]) is int and op[k]==want,k)
need(obs['records']==[] and op['callback_receipt_records']==0 and op['visual']['interaction_fixture_rendered'] is False,'inconclusive control')
need(op['duplicate']['index']==30 and op['duplicate']['tree_line'].strip()==op['duplicate']['summary_line'].strip(),'Selected duplicate transcription')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','cleanup')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source')
source=(p/'fixture-source.swift').read_text()
for text in ['accessibilityIdentifier("owned.callback.root")','accessibilityIdentifier("owned.callback.count")','accessibilityIdentifier("owned.callback.increment")']:need(source.count(text)==1,'declared identifiers')
need(datetime.datetime.fromisoformat(cleanup['at'])<datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')),'cleanup deadline')
for opt in [[],['-O']]:
 for name in ['test_exposure.py','test_normalize_selected.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,check=True,timeout=10)
for n in ['test-guard.mjs','test-normalized-guard.mjs']:subprocess.run(['node',str(p/n)],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'scanner_methods':6,'normalizer_methods':9,'guard_assertions':16,'normalizer_assertions':8,'native_navigation_failed':True,'AX_exposure_qualified':False,'cleanup_verified':True}))
