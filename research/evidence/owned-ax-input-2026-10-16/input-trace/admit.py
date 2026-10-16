"""Scoped owned-action receipt gate; native Canvas routing remains unqualified."""
import copy,json
from pathlib import Path
from geometry_admit import admitted as geometry_admitted

def admitted(fixture,inventory,root):
 def need(v):
  if not v:raise ValueError('Owned interaction admission rejected')
 def integer(v,n):return type(v) is int and v==n
 f=json.loads(fixture['record']['stdout'])
 need(f['status']=='owned_interaction_control_admitted' and f['admitted'] is True and f['scope']=='owned-two-window-AXPress-interaction')
 # Explicit status adaptation solely to reuse the unchanged geometry/cleanup gate.
 g=copy.deepcopy(fixture);body=copy.deepcopy(f);body['status']='owned_geometry_correlation_admitted';g['record']['stdout']=json.dumps(body)
 geometry_admitted(g,inventory,root)
 steps=f['interaction_steps'];need(type(steps) is list and [s['kind'] for s in steps]==['selection','positive','stale','overlap'])
 target=Path(root,'b.xcodeproj').as_uri()+'/'
 ids={r['document']:r['fixture_window_id'] for r in f['phases'][0]['rows']}
 def counts(v,b):need(type(v) is dict and set(v)=={'a','b','unknown'} and integer(v['a'],0) and integer(v['b'],b) and integer(v['unknown'],0))
 for index,s in enumerate(steps):counts(s['counts'],0 if index==0 else 1)
 counts(f['callback_counts'],1)
 for s in [steps[0]['validation'],steps[1]['result']['validation']]:
  need(s['accepted'] is True and s['reason']=='validated' and s['document']==target and type(s['native_window_id']) is int and s['native_window_id']==ids[target] and s['AXPress_available'] is True and integer(s['AX_action_names_error'],0) and type(s['AX_action_name_count']) is int and 1<=s['AX_action_name_count']<=32)
 positive=steps[1]['result'];need(positive['action_attempted'] is True and integer(positive['AX_press_error'],0))
 for s,reason in [(steps[2],'binding_changed'),(steps[3],'CG_identity_not_unique')]:
  v=s['result'];need(v['action_attempted'] is False and 'AX_press_error' not in v and v['validation']['accepted'] is False and v['validation']['reason']==reason)
 matches=steps[3]['result']['validation']['candidates'];need(type(matches) is list and len(matches)==2 and all(type(x) is int for x in matches) and set(matches)==set(ids.values()))
 return {'owned_AXPress_callback_control_observed':True,'target_document':target,'positive_callback_counts':f['callback_counts'],'stale_and_overlap_abstained':True,'native_input_qualified':False,'live_Xcode_route_qualified':False,'scope':'One owned public AXPress callback/control run only'}
if __name__=='__main__':
 p=Path(__file__).parent;v=admitted(json.loads((p/'fixture-record.json').read_text()),json.loads((p/'inventory-record.json').read_text()),str(p/'owned-documents'));(p/'admission.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
