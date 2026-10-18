import json,hashlib,subprocess,sys,datetime
from pathlib import Path
from path_binding import validate_binding
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved local pin')
b=validate_binding(json.loads((p/'path-binding.json').read_text()))
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());cleanup=json.loads((p/'reconciliation-cleanup.json').read_text())
need(op['deadline_met'] is False and op['original_plan_closed'] is True and op['cleanup_reconciled_late'] is True and op['callback_access_qualified'] is False,'failed plan scope')
for n in ['refresh_clicks','preview_selection_clicks','increment_clicks','renderpreview_calls','receipt_observations_during_plan']:
 need(type(op[n]) is int and op[n]==0,'unexecuted '+n)
need(type(op['workspace_opens']) is int and op['workspace_opens']==1,'owned opening')
need(type(cleanup['owned_workspace_windows']) is int and cleanup['owned_workspace_windows']==0,'zero windows')
need(cleanup['windows']['structuredContent']['message']=='No workspace windows found','broker cleanup')
need(cleanup['original_deadline_missed'] is True and cleanup['experiment_reopened'] is False,'late reconciliation scope')
need(datetime.datetime.fromisoformat(cleanup['at'])>datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')),'late time')
source=p/'workspace/Sources/PreviewLab/PreviewLab.swift'
need(hashlib.sha256(source.read_bytes()).hexdigest()==plan['source_sha256']==cleanup['source_sha256'],'source unchanged')
need(source.read_bytes()==(p/'ReceiptWriter.swift').read_bytes()+b'\n'+(p/'PreviewFixture.swift').read_bytes(),'source combination')
need(not(p/'receipt-observation.json').exists(),'no callback observation')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_path_binding.py')],capture_output=True,check=True,timeout=15)
print(json.dumps({'verified':True,'files':len(seal['files']),'offline_methods':12,'native_plan_accepted':False,'late_cleanup_verified':True,'callback_access_qualified':False}))
