"""Owned native-producer consistency gate; no live action authority."""
import json,math
from pathlib import Path

def admitted(fixture,inventory,root):
 def need(v):
  if not v:raise ValueError('Owned fixture admission rejected')
 def integer(v,n):return type(v) is int and v==n
 def rect(v):
  need(type(v) is dict and set(v)=={'X','Y','Width','Height'})
  need(all(type(x) in (int,float) and math.isfinite(x) for x in v.values()))
  need(v['Width']>0 and v['Height']>0)
  return v
 for row in [fixture,inventory]:
  r=row['record'];p=r['report']
  need(row['error'] is None and integer(p['target_code'],0) and p['failure'] is None and p['drained'] is True and integer(p['remaining_observed'],0) and r['emergencyClosed'] is False and r['privateAbortRequested'] is False)
 f=json.loads(fixture['record']['stdout']);i=json.loads(inventory['record']['stdout'])
 need(type(f['pid']) is int and f['pid']>1 and integer(i['target_pid'],f['pid']) and integer(i['owned_on_screen_windows'],0))
 need(f['admitted'] is True and f['status']=='owned_geometry_correlation_admitted' and integer(f['own_on_screen_after_close'],0))
 docs={Path(root,n+'.xcodeproj').as_uri()+'/' for n in ['a','b']}
 need(type(f['phases']) is list and len(f['phases'])==3);bindings=None;ax_orders=[];cg_orders=[]
 for index,p in enumerate(f['phases']):
  need(p['status']=='observed' and integer(p['own_cg_windows'],2) and len(p['rows'])==2)
  need(integer(p['AX_windows_error'],0) and integer(p['AX_window_count'],2))
  need({r['document'] for r in p['rows']}==docs)
  current={r['document']:r['fixture_window_id'] for r in p['rows']}
  need(all(type(x) is int and x>0 for x in current.values()) and len(set(current.values()))==2)
  if bindings is None:bindings=current
  need(current==bindings);ax_orders.append([r['document'] for r in p['rows']]);cg=None
  for r in p['rows']:
   need(r['button_ancestor_matches'] is True)
   g=r['AX_geometry'];need(integer(g['position_error'],0) and integer(g['size_error'],0) and integer(g['position_AX_type'],1) and integer(g['size_AX_type'],2));a=rect(g['AX_rect'])
   c=r['CG_geometry'];need(type(c) is list and len(c)==2)
   need(all(type(x['id']) is int for x in c) and {x['id'] for x in c}==set(bindings.values()))
   for x in c:rect(x['rect'])
   if cg is None:cg=c
   need(c==cg)
   ids=r['candidate_ids'];need(type(ids) is list and all(type(x) is int for x in ids))
   need(ids==[x['id'] for x in c if x['rect']==a])
   if index<2:need(ids==[bindings[r['document']]] and r['unique_candidate_equals_fixture'] is True)
   else:need(len(ids)==2 and set(ids)==set(bindings.values()) and r['unique_candidate_equals_fixture'] is False)
  cg_orders.append([x['id'] for x in cg])
 need(ax_orders[1]==ax_orders[0][::-1] and cg_orders[1]==cg_orders[0][::-1])
 return {'scope':'owned public geometry correlation only','owned_fixture_admitted':True,'actual_AX_and_CG_reorder':True,'immediate_close_count':0,'postexit_own_windows':0,'native_input_qualified':False,'live_Xcode_route_qualified':False}

if __name__=='__main__':
 root=Path(__file__).parent
 result=admitted(json.loads((root/'fixture-record.json').read_text()),json.loads((root/'inventory-record.json').read_text()),str(root/'owned-documents'))
 (root/'admission.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
