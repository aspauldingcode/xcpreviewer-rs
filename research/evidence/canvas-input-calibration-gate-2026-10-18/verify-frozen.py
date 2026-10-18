from pathlib import Path
import json,hashlib,sys,subprocess
p=Path(__file__).resolve().parent
def need(x,m):
 if not x:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'proposed local pin')
plan=json.loads((p/'experiment.json').read_text());closed=json.loads((p/'closure.json').read_text());frame=json.loads((p/'coordinate-frame.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior']
for k in ['workspace_opens','coordinate_clicks','native_jobs','receipt_observations']:need(type(closed[k]) is int and closed[k]==0,k)
need(closed['plan_closed'] is True and closed['deadline_renewed'] is False and closed['source_restored_to_prior_verified_fixture'] is True,'closed proposal')
need(closed['source_restored_sha256']==prior['source_sha256']==hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest(),'restore association')
need(closed['windows']['structuredContent']['message']=='No workspace windows found','zero windows')
need(frame['status']=='unavailable' and frame['api']=='cua App.click(Vec2)','frame remains unavailable')
need((p/'fixture-source.swift').read_text()==(p/'fixture-before.swift').read_text().replace('20d74faa8f664eca9618ae35ac7b3141',plan['nonce']),'prepared nonce-only source change')
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==plan['source_sha256'],'prepared source pin')
for n in ['receipt-observation-1.json','receipt-observation-2.json','receipt-observation-3.json','build-association.json','validated-1.json','validated-2.json','validated-3.json','bridge-before.json','cleanup.json']:need(not(p/n).exists(),'unexpected native artifact')
for opt in [[],['-O']]:
 for name in ['test_geometry.py','test_validate_receipts.py']:subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,check=True,timeout=10)
for n in ['test-guard.mjs','test-input-gate.mjs']:subprocess.run(['node',str(p/n)],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'geometry_methods':5,'synthetic_receipt_methods':6,'guard_assertions':16,'model_gate_assertions':19,'native_jobs':0,'coordinate_frame_verified':False,'input_qualified':False}))
