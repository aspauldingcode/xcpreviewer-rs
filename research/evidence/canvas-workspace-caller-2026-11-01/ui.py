from pathlib import Path
import json,re,hashlib,sys
w=Path(__file__).parent
if len(sys.argv)>1:
 raw=Path(sys.argv[1]).read_text();nodes={};stack=[]
 for line in raw.splitlines():
  m=re.match(r'^(\t*)(\d+) (.*)$',line)
  if not m:continue
  depth=len(m[1]);key=int(m[2]);text=m[3]
  while stack and stack[-1][0]>=depth:stack.pop()
  nodes[key]={'text':text,'parent':stack[-1][1] if stack else None};stack.append((depth,key))
 def find(term):
  matches=[k for k,v in nodes.items() if term in v['text']];assert len(matches)==1,(term,len(matches));return matches[0]
 def ancestors(k):
  out=[]
  while k is not None:out.append(k);k=nodes[k]['parent']
  return out
 pin=find('Description: Pin Preview,');live=find('Description: Live,');common=next(k for k in ancestors(pin) if k in ancestors(live));assert nodes[common]['text']=='container'
 previews=[]
 for name in ['Primary layers','Text and interaction','Layout edit']:
  k=find('text '+name);assert common in ancestors(k);previews.append(name)
 for label in ['Selectable','Variants','Device Settings']:
  assert common in ancestors(find('Description: '+label+','))
 scheme=find('pop up button Description: Active Scheme, Value: PreviewLab');destination=find('pop up button Description: Active Run Destination, Value: My Mac');assert any('toolbar'==nodes[k]['text'] for k in ancestors(scheme)) and any('toolbar'==nodes[k]['text'] for k in ancestors(destination))
 fixture=Path('/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b');assert str(fixture/'PreviewLab.xcodeproj') in raw
 source=fixture/'Sources/PreviewLab/PreviewLab.swift';project=fixture/'PreviewLab.xcodeproj/project.pbxproj'
 receipt=json.loads((w/'ui-receipt.json').read_text());assert receipt['fullSnapshot'] and receipt['within15SecondReadBudget'] and all(receipt[k] for k in ['ownedFixturePathPresent','activeSchemePresent','activeDestinationPresent','readyPresent','threePreviewLabels','liveModeSelected'])
 p={'fixture':'Owned PreviewLab project','scheme':'PreviewLab','destination':'My Mac','preview_labels':previews,'preview_labels_and_controls_share_canvas_ancestor':True,'active_selectors_under_toolbar':True,'live_selected':'(selected)' in nodes[live]['text'],'pin_selected':'(selected)' in nodes[pin]['text'],'other_canvas_controls':['Selectable','Variants','Device Settings'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'project_sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'raw_full_ax_sha256':hashlib.sha256(raw.encode()).hexdigest(),'read_only':True,'input_actions':0,'build_refresh_actions':0,'scope':'Retained full native AX observation and owned filesystem identities. No private function execution/causal trace or build/refresh/state transition.'};(w/'native-ui-projection.json').write_text(json.dumps(p,indent=2)+'\n')
p=json.loads((w/'native-ui-projection.json').read_text());assert p['scheme']=='PreviewLab' and p['destination']=='My Mac' and p['preview_labels_and_controls_share_canvas_ancestor'] and p['active_selectors_under_toolbar'] and p['live_selected'] and p['read_only'] and p['input_actions']==p['build_refresh_actions']==0
print(json.dumps({'retained_native_ui_projection_valid':True,'retained_full_ax_parsed':len(sys.argv)>1,'native_ui_reobserved':False,'scope':'Receipt validation only unless an explicitly supplied retained full AX input is parsed.'}))
