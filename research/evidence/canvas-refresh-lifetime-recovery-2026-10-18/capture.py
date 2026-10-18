"""Three bounded public Xcode RenderPreview calls; no native private IPC claim."""
import datetime,hashlib,json,shutil,sys,time
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');root=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.xcodebridge import BrokerClient
from decode import decode
from bindings import payload,owned_tab
from identity import snapshot,classify
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
workspace=r/'research/build/preview-workspaces/refresh-lifetime-20261018'
deadline=datetime.datetime(2026,10,18,17,12,0,tzinfo=datetime.timezone.utc).timestamp()
with Controller().lock():
 for name,digest in json.loads((root/'approved-pins.json').read_text()).items():
  if sha(root/name)!=digest:raise ValueError('approved pin changed')
 if sha(workspace/'Sources/PreviewLab/PreviewLab.swift')!=sha(root/'probe.swift'):raise ValueError('source changed')
 b=BrokerClient(timeout=55)
 windows=b.request('tools/call',{'name':'XcodeListWindows','arguments':{}})
 (root/'window-binding.json').write_text(json.dumps(windows,indent=2)+'\n')
 tab=owned_tab(windows,workspace/'PreviewLab.xcodeproj')
 rows=[];after_samples=[];before_samples=[]
 for phase in range(3):
  if time.time()+70>deadline:raise ValueError('absolute budget reserve expired')
  if sha(workspace/'Sources/PreviewLab/PreviewLab.swift')!=sha(root/'probe.swift'):raise ValueError('source changed')
  args={'tabIdentifier':tab,'sourceFilePath':'PreviewLab/Sources/PreviewLab/PreviewLab.swift','timeout':45}
  start=time.monotonic();record={'phase':phase,'request':{'name':'RenderPreview','arguments':args},'source_sha256':sha(root/'probe.swift'),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  try:
   if phase:
    prior=after_samples[-1]['root'];before=snapshot(prior['pid'],prior['identity']);record['before_identity']=before;before_samples.append(before)
    if before['status']!='observed' or before['root'] is None or before['root']['state']!='L':raise ValueError('Prior sampled identity unavailable; stop without liveness/reclamation inference')
   if time.time()+60>deadline:raise ValueError('absolute deadline expired after identity prerequisite')
   value=b.request('tools/call',{'name':'RenderPreview','arguments':args});record['response']=value
   data=payload(value)
   if data.get('errors') or not data.get('previewSnapshotPath'):raise ValueError('missing/error snapshot')
   name='phase%d.png'%phase;target=root/name
   if target.exists():raise ValueError('output exists')
   shutil.copy2(data['previewSnapshotPath'],target);record['png_sha256']=sha(target);record['decoded']=decode(target)
   after=snapshot(record['decoded']['pid']);record['after_identity']=after;after_samples.append(after)
   if after['status']!='observed' or after['root'] is None or after['root']['state']!='L':raise ValueError('Snapshot process identity unavailable; stop without liveness/reclamation inference')
   record['status']='measured'
  except Exception as e:
   record.update(status='failed',error_type=type(e).__name__,error=str(e));raise
  finally:
   record['elapsed_seconds']=time.monotonic()-start
   with (root/('phase%d.json'%phase)).open('x') as f:json.dump(record,f,indent=2);f.write('\n')
  rows.append(record['decoded'])
 result={'scope':'RenderPreview request boundary only, source unchanged, no UI interaction or edit/reset policy claim','measurements':rows,'pid_same_across_requests':len({x['pid'] for x in rows})==1,'state_token_same_across_requests':len({x['state_token_hex'] for x in rows})==1,'visible_rgba_bytes_checked':sum(x['rgba_bytes_checked'] for x in rows),'state_tokens_are_measurements_not_independent_goldens':True,'private_canvas_transport_qualified':False,'general_state_retention_qualified':False,'identity_observations':classify(after_samples,before_samples)}
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
