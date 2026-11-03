"""Check recorded native calls and UI artifacts; does not run Xcode."""
from pathlib import Path
import json,re,collections,hashlib
from PIL import Image,ImageStat

def verify(root):
 r=Path(root);rows=[json.loads(x) for x in (r/'run1/events.jsonl').read_text().splitlines()]
 assert not any(x['stage']=='failed' or x.get('message',{}).get('type')=='error' for x in rows)
 calls=[x['message']['payload'] for x in rows if x['stage']=='script' and x.get('message',{}).get('type')=='send']
 assert not any(x['event']=='overflow' for x in calls)
 ready=[x for x in calls if x['event']=='hooks-ready'];assert len(ready)==1 and ready[0]['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93' and ready[0]['ui_uuid']=='0d87b0e2f4453035a9b6b1cf8230e015'
 enters={x['id']:(i,x) for i,x in enumerate(calls) if x['event']=='enter'};returns={x['id']:(i,x) for i,x in enumerate(calls) if x['event']=='return'}
 assert len(enters)==sum(x['event']=='enter' for x in calls) and len(returns)==sum(x['event']=='return' for x in calls)
 counts=collections.Counter(x['function'] for _,x in enters.values());assert counts['removed-locations']==0 and counts['preview-state-destroy']>0
 for ident,(i,x) in enters.items():
  if x['function']=='preview-state-destroy':assert ident not in returns;continue
  assert ident in returns;end,y=returns[ident];assert i<end and x['thread']==y['thread'] and x['function']==y['function'] and x['phase']==y['phase']
 assert set(returns)<=set(enters)
 collectors=0
 for ident,(start,x) in enters.items():
  if x['function']!='collector':continue
  collectors+=1;end=returns[ident][0]
  nested=[(i,y) for i,y in enumerate(calls) if start<i<end and y['event']=='enter' and y['thread']==x['thread'] and y['function'] in ['providers','registries']]
  assert [y['function'] for _,y in nested]==['providers','providers','registries','registries']
  assert [y['caller_offset'] for _,y in nested]==['0x29fb0','0x29fc4','0x2a100','0x2a114']
  assert all(y['caller_module']=='PreviewsScenes' for _,y in nested)
  for n,(i,y) in enumerate(nested):assert i<returns[y['id']][0]<(nested[n+1][0] if n<3 else end)
 assert collectors>0 and counts['providers']==counts['registries']==2*collectors
 for ident,(start,x) in enters.items():
  if x['function']!='canvas-content-destroy':continue
  end=returns[ident][0];nested=[y for i,y in enumerate(calls) if start<i<end and y['event']=='enter' and y['function']=='preview-state-destroy' and y['thread']==x['thread']]
  assert len(nested)==1 and nested[0]['caller_module']=='PreviewsUI' and nested[0]['caller_offset']=='0x23ee8'
 assert counts['canvas-content-destroy']==counts['preview-state-destroy']
 for name in ['pinning-didset','preview-update']:assert counts[name]>0
 assert all(any(x['event']=='enter' and x['function']=='collector' and x['phase']==phase for x in calls) for phase in ['edit','restore'])
 tabs=lambda s:re.findall(r'^\s*\d+ text (Primary layers|Text and interaction|Layout edit|Runtime addition)$',s,re.M)
 images={}
 for run,added,restored in [('run1','added-ready-ax.txt','restored-ax.txt'),('no-hooks','added-ax.txt','restored-settled-ax.txt')]:
  p=r/run;events=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
  assert events[-1]['stage']=='session-ended-no-target-termination' and events[-1]['source_restored']
  assert [x['stage'] for x in events if x['stage']!='script']==['capture-ready','source-edit-begin','source-declaration-added','source-declaration-removed','session-ended-no-target-termination']
  assert next(x for x in events if x['stage']=='capture-ready')['hooks']==(run=='run1')
  if run=='no-hooks':assert not any(x['stage']=='script' for x in events)
  source=(p/'source-before.swift').read_bytes();assert hashlib.sha256(source).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  after=source+b'\n#Preview("Runtime addition", traits: .fixedLayout(width: 80, height: 40)) {\n    Color.orange.frame(width: 80, height: 40)\n}\n'
  assert next(x for x in events if x['stage']=='source-declaration-added')['sha256']==hashlib.sha256(after).hexdigest()
  assert tabs((p/'baseline-ax.txt').read_text())==['Primary layers','Text and interaction','Layout edit']
  assert tabs((p/added).read_text())==['Primary layers','Text and interaction','Layout edit','Runtime addition']
  assert tabs((p/restored).read_text())==['Primary layers','Text and interaction','Layout edit']
  restored_image='restored.png' if run=='run1' else 'restored-settled.png'
  def mean(n):
   im=Image.open(p/n).convert('RGB');assert im.size==(2802,1804);return ImageStat.Stat(im.crop((2220,970,2280,990))).mean
  selected,settled=mean('selected.png'),mean(restored_image);assert selected[0]>selected[1]>selected[2] and settled[2]>settled[1] and settled[0]>settled[1] and selected!=settled
  images[run]={'selected_rgb_mean':selected,'restored_rgb_mean':settled}
 o=json.loads((r/'observations.json').read_text());assert not o['native_object_lifetimes_verified'] and not o['native_resource_release_verified'] and not o['preview_state_return_verified'] and o['source_restored_controller_available']
 return {'recorded_native_entries':dict(counts),'collector_calls_with_two_providers_then_two_registries':collectors,'preview_state_returns_observed':0,'removed_location_entries_observed':0,'image_regions':images,'artifact_reader_reran_native':False,'native_resource_release_verified':False}
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1]),indent=2))
