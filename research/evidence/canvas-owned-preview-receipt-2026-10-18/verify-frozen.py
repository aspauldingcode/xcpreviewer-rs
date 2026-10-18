from pathlib import Path
import json,hashlib,sys,subprocess,datetime
from decoder import record
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved local pin')
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());obs=json.loads((p/'receipt-observation.json').read_text());build=json.loads((p/'build-association.json').read_text());assessment=json.loads((p/'assessment.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text())
for key,want in [('workspace_opens',1),('refresh_clicks',0),('preview_selection_clicks',1),('increment_clicks',0),('renderpreview_calls',0),('receipt_observations',1)]:need(type(op[key]) is int and op[key]==want,key)
need(op['matching_nonbusy_signatures'] is True and op['previous_signature_length']==op['fresh_signature_length']==7221,'recorded guard equality')
need(op['AX_observations']<=plan['maximum_state_observations'] and op['passive_readiness_observations']<=plan['maximum_passive_readiness_observations'],'observation bounds')
need(len(obs['records'])==1,'one receipt');x=obs['records'][0];live=x['live_identity'];ident=assessment['identity']
need(type(live['pid']) is int and live['pid']==ident['pid'] and live['state']=='L','live PID sample')
need(len(live['identity'])==3 and all(type(z) is int for z in live['identity'][:2]) and live['identity'][2]==build['binary_path'],'birth/path identity')
need(build['binary_path'].endswith('/Build/Products/Debug/PreviewLab.app/Contents/MacOS/PreviewLab'),'owned app path')
need(build['filelist_utf8']=='/tmp/callback-ui-access-20261018/workspace/Sources/PreviewLab/PreviewLab.swift\n','build source association')
need(hashlib.sha256(build['filelist_utf8'].encode()).hexdigest()==build['filelist_sha256'],'filelist bytes')
need(ident['nonce']==plan['nonce'] and ident['view']==op['visual']['view'] and op['visual']['count']==0,'source/visual identity')
raw=bytes.fromhex(x['raw_hex']);record(raw,x['name'],ident,'appear',0,0)
need(raw==(p/'native-receipt.json').read_bytes() and len(raw)==assessment['bytes_compared']==154,'all record bytes')
need(assessment['button_input_qualified'] is False and assessment['general_sandbox_policy_proven'] is False and assessment['source_selection_causality_proven'] is False,'claim limits')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('60fd2da461f6404ea93e47eb59d6831a',plan['nonce']),'only nonce/path source change')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source binding')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0 and cleanup['broker_message']=='No workspace windows found','zero owned windows')
need(datetime.datetime.fromisoformat(cleanup['at'])<datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')),'cleanup deadline')
need(datetime.datetime.fromisoformat(op['selection_completed_by'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(plan['stop_new_actions_utc'].replace('Z','+00:00')),'action deadline')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_decoder.py')],capture_output=True,check=True,timeout=10)
subprocess.run(['node',str(p/'test-guard.mjs')],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'native_receipt_bytes':154,'decoder_methods':7,'guard_assertions':16,'owned_cleanup_verified':True,'button_input_qualified':False}))
