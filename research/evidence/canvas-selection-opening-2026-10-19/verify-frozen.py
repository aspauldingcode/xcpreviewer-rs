from pathlib import Path
import hashlib,json,subprocess,sys,datetime
p=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)
s=json.loads((p/'seal.json').read_text());need({x.name for x in p.iterdir() if x.name!='seal.json'}==set(s['files']),'closed file set')
for n,h in s['files'].items():need((p/n).is_file() and not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
for n,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not n.startswith('/'):need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin '+n)
e=json.loads((p/'experiment.json').read_text());o=json.loads((p/'operation.json').read_text());r=json.loads((p/'registry-observation.json').read_text());c=json.loads((p/'cleanup.json').read_text());prior=json.loads((p/'selection.json').read_text())['prior']
need(hashlib.sha256((p/'fixture-source.swift').read_bytes()).hexdigest()==e['source_sha256']==c['source_sha256']==r['source_sha256'],'source')
need(hashlib.sha256((p/'fixture-before.swift').read_bytes()).hexdigest()==prior['source_sha256'],'prior source')
need((p/'fixture-before.swift').read_text().replace('9fa2e73bf8774c5280215a4b1afe661c',e['nonce'])==(p/'fixture-source.swift').read_text(),'nonce-only source delta')
need(r['session']==e['nonce'] and r['history']==[] and r['duplicate_error']=='session already bound' and r['context_unchanged'] is True,'registry')
for k,w in [('open_attempts',1),('manual_AX_observations',2),('driver_AX_observations',0),('readiness_samples',0),('refresh_clicks',0),('preview_selection_clicks',0),('CUA_inventory_calls',0),('getApp_calls',0),('host_app_selections',0),('host_app_launches',0),('increment_clicks',0),('coordinate_clicks',0),('renderpreview_calls',0),('receipt_observations',0)]:need(type(o[k]) is int and o[k]==w,k)
for k in ['owned_workspace_open_observed','native_retry','callback_baseline_qualified','controller_terminal','sampler_failed','open_clickCount_explicit']:need(o[k] is False,k)
for k in ['experiment_failed','outer_closed','actual_nonce_cross_call_duplicate_rejected','strict_selection_registry_bootstrap_native_used']:need(o[k] is True,k)
need(o['post_click_window']=='Welcome to Xcode','observed postcondition')
parse=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
need(parse(c['at'])<parse(e['stop_new_actions_utc'])<parse(e['deadline_utc']),'fixed cutoff cleanup')
need(r['stopWall']==parse(e['stop_new_actions_utc']).timestamp() and r['cleanupWall']==parse(e['deadline_utc']).timestamp(),'registry deadlines')
need(type(c['owned_workspace_windows']) is int and c['owned_workspace_windows']==0 and c['broker_message']=='No workspace windows found','zero')
for n,count in [('test-selection-only.mjs',13),('test-selection-registry.mjs',11),('test-session-driver.mjs',6),('test-owned-opener.mjs',12)]:
 x=subprocess.run(['node',str(p/n)],check=True,capture_output=True,text=True,timeout=10);v=json.loads(x.stdout);need(type(v['cases']) is int and v['cases']==count and v['native_execution'] is False,n)
x=subprocess.run(['node',str(p/'test-caller.mjs')],check=True,capture_output=True,text=True,timeout=10);need(json.loads(x.stdout)['next_call_duplicate_rejected'] is True,'literal caller')
for opt in [[],['-O']]:
 for n in ['test_decoder.py','test_exposure.py']:subprocess.run([sys.executable,*opt,'-B',str(p/n)],check=True,capture_output=True,timeout=10)
x=json.loads(json.loads((p/'graph-loop-inspection.json').read_text())['stdout']);need(x['execution_started'] is False and not x['candidates'],'graph')
x=json.loads(json.loads((p/'workgraph-inspection.json').read_text())['stdout']);need(x['milestone1_complete'] is False and x['milestone2_complete'] is False,'milestones')
print(json.dumps({'verified':True,'files':len(s['files']),'opening_attempts':1,'observed_workspace_opening':False,'native_readiness_exercised':False,'offline_opener_cases':12,'cleanup_verified':True}))
