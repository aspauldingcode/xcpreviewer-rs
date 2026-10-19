from pathlib import Path
import hashlib,json,datetime,subprocess,sys
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
pins=json.loads((p/'approved-pins.json').read_text())
for n,h in pins.items():
 if n.startswith('/'):continue
 f=p/('match-before-scope-fix.py' if n=='match.py' else n);need(hashlib.sha256(f.read_bytes()).hexdigest()==h,'approved pin '+n)
need(pins['/Users/8amps/xcpreviewer-rs/research/build/libproc-observer/owned-process-snapshot']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5','sealed helper identity')
need((p/'match-before-scope-fix.py').read_text().replace('prior owned PID absent at this sample','prior owned PID not emitted; absence versus unobservable remains unresolved')==(p/'match.py').read_text(),'postexecution reporting-only correction')
plan=json.loads((p/'experiment.json').read_text());op=json.loads((p/'operation.json').read_text());ob=json.loads((p/'process-observation.json').read_text());apps=json.loads((p/'app-inventory.json').read_text());closure=json.loads((p/'closure.json').read_text());assessment=json.loads((p/'assessment.json').read_text());selection=json.loads((p/'selection.json').read_text())
for k,w in [('public_snapshots',1),('CUA_inventory_calls',1),('app_selections',0),('getApp_calls',0),('workspace_opens',0),('clicks',0),('receipt_reads',0),('signals',0),('app_launches',0)]:need(type(op[k]) is int and op[k]==w,k)
need(ob['returncode']==0 and ob['process'] is None and ob['expected']==plan['expected'] and ob['unrelated_descendant_rows_retained'] is False,'root not emitted')
need(apps['filtered_apps']==[] and apps['CUA_inventory_calls']==1,'empty filtered inventory')
from match import compare
need(compare(plan['expected'],ob['process'],apps['filtered_apps'])==assessment,'independent comparison')
need(assessment['metadata_binding_available'] is False and assessment['native_action_authorized'] is False and op['global_PID_absence_proven'] is False,'scope')
need(type(closure['owned_workspace_windows']) is int and closure['owned_workspace_windows']==0 and closure['source_sha256']==selection['current_source_sha256']==selection['prior']['source_sha256'],'closure/source')
need(closure['windows']['structuredContent']['message']=='No workspace windows found','broker zero')
parse=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
for t in [ob['at'],apps['at'],closure['at']]:need(parse(t)<parse(plan['deadline_utc']),'deadline')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_match.py')],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'matcher_methods':8,'public_snapshot_root_emitted':False,'filtered_app_entries':0,'global_PID_absence_proven':False,'native_action_authorized':False,'owned_workspace_windows':0}))
