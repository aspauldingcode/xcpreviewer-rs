from pathlib import Path
import json,hashlib,subprocess,sys,datetime
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
for name,h in seal['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError(name)
from window_binding import bind
plan=json.loads((p/'experiment.json').read_text());source=Path(plan['workspace']).parent/'Sources/PreviewLab/PreviewLab.swift'
value=bind((p/'owned-window-projection.ax.txt').read_text(),json.loads((p/'windows-2.json').read_text()),plan['workspace'],source)
if value['tab']!='windowtab4' or value['close_index']!=93:raise ValueError('binding')
cleanup=json.loads((p/'cleanup.json').read_text())
if cleanup['owned_workspace_windows']!=0 or cleanup['broker_message']!='No workspace windows found' or cleanup['source_sha256']!=plan['source_sha256']:raise ValueError('cleanup')
if hashlib.sha256((p/'probe.swift').read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('source')
if datetime.datetime.fromisoformat(cleanup['at'])>=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')):raise ValueError('deadline')
obs=json.loads((p/'operator-observations.json').read_text())
if obs['window_opens']!=1 or obs['navigation_attempts']!=1 or obs['increment_clicks']!=0 or obs['renderpreview_calls']!=0 or obs['increment_binding_qualified'] is not False or obs['explicit_interaction_preview_selected'] is not False:raise ValueError('scope')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_window_binding.py')],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'synthetic_methods':6,'owned_windows_after':0,'input_qualified':False,'full_AX_or_pixels_retained':False,'native_execution':False}))
