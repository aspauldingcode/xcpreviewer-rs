"""Combined frozen admission; phase exit codes alone are insufficient."""
import json
from pathlib import Path

def admitted(fixture,inventory,root):
 def need(v):
  if not v:raise ValueError('Owned fixture admission rejected')
 for row in [fixture,inventory]:
  r=row['record'];p=r['report']
  need(row['error'] is None and p['target_code']==0 and type(p['target_code']) is int and p['failure'] is None and p['drained'] is True and p['remaining_observed']==0 and r['emergencyClosed'] is False and r['privateAbortRequested'] is False)
 f=json.loads(fixture['record']['stdout']);i=json.loads(inventory['record']['stdout'])
 need(type(f['pid']) is int and f['pid']>1)
 need(type(i['target_pid']) is int and i['target_pid']==f['pid'])
 need(type(i['owned_on_screen_windows']) is int and i['owned_on_screen_windows']==0)
 need(f['admitted'] is True and f['status']=='owned_geometry_correlation_admitted' and f['own_on_screen_after_close']==0)
 docs={Path(root,n+'.xcodeproj').as_uri()+'/' for n in ['a','b']}
 need(len(f['phases'])==3);bindings=None
 for index,p in enumerate(f['phases']):
  need(p['status']=='observed' and p['own_cg_windows']==2 and len(p['rows'])==2)
  need({r['document'] for r in p['rows']}==docs)
  current={r['document']:r['fixture_window_id'] for r in p['rows']}
  need(all(type(x) is int and x>0 for x in current.values()) and len(set(current.values()))==2)
  if bindings is None:bindings=current
  need(current==bindings)
  for r in p['rows']:
   need(r['button_ancestor_matches'] is True)
   ids=r['candidate_ids'];need(all(type(x) is int and x>0 for x in ids))
   if index<2:need(ids==[bindings[r['document']]] and r['unique_candidate_equals_fixture'] is True)
   else:need(len(ids)==2 and set(ids)==set(bindings.values()) and r['unique_candidate_equals_fixture'] is False)
 return {'scope':'owned public geometry correlation only','owned_fixture_admitted':True,'postexit_own_windows':0,'native_input_qualified':False,'live_Xcode_route_qualified':False}

if __name__=='__main__':
 import sys
 root=Path(__file__).parent
 result=admitted(json.loads((root/'fixture-record.json').read_text()),json.loads((root/'inventory-record.json').read_text()),str(root/'owned-documents'))
 (root/'admission.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
