from pathlib import Path
import hashlib,json,subprocess,sys,datetime
p=Path(__file__).resolve().parent;seal=json.loads((p/'seal.json').read_text())
for n,h in seal['files'].items():
 f=p/n
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError(n)
plan=json.loads((p/'experiment.json').read_text());obs=json.loads((p/'observations.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text())
if obs['window_opens']!=1 or obs['refresh_clicks']!=1 or obs['title_clicks']!=1 or obs['increment_clicks']!=0 or obs['renderpreview_calls']!=0 or obs['input_qualified'] is not False:raise ValueError('scope')
if obs['AX_observations_including_welcome_and_cleanup']>plan['maximum_state_observations'] or obs['passive_readiness_observations']>3:raise ValueError('observation budget')
stop=datetime.datetime.fromisoformat(plan['stop_new_actions_utc'].replace('Z','+00:00'))
for key in ['refresh_at','title_click_at']:
 if datetime.datetime.fromisoformat(obs[key].replace('Z','+00:00'))>=stop:raise ValueError('action deadline')
if datetime.datetime.fromisoformat(cleanup['at'])>=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')):raise ValueError('cleanup deadline')
if cleanup['owned_workspace_windows']!=0 or cleanup['broker_message']!='No workspace windows found' or cleanup['source_sha256']!=plan['source_sha256'] or hashlib.sha256((p/'probe.swift').read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('cleanup/source')
from bindings import owned_tab
if owned_tab(json.loads((p/'windows-2.json').read_text()),plan['workspace'])!='windowtab6':raise ValueError('broker')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_window_binding.py')],capture_output=True,check=True,timeout=10)
for name in ['test-stable-guard.mjs','test-preview-selection.mjs','replay-selection.mjs']:subprocess.run(['node',str(p/name)],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'python_methods':6,'javascript_assertions':26,'owned_workspace_windows_after':0,'native_execution':False,'input_qualified':False,'visual_findings_operator_only':True}))
