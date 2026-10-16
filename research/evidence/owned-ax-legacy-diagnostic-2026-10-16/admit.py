"""Admit a bounded diagnostic attached to an expected rejected owned experiment.

This never admits the rejected projection, subtree absence, or input eligibility.
"""
import copy,json,re
from pathlib import Path
from tree_admit import receipt,parsed,need,integer

def admitted(fixture,inventory,root):
 need(type(fixture['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',fixture['binary_sha256']) is not None)
 p=fixture['record']['report'];need(fixture['error']=='Error: Observed compiler failed: 78' and integer(p['target_code'],78))
 # Explicit expected-failure adaptation reuses raw byte/PID/drain checks only.
 a=copy.deepcopy(fixture);a['error']=None;a['record']['report']['target_code']=0;f=receipt(a);i=receipt(inventory)
 need(f['status']=='owned_fixture_rejected' and f['admitted'] is False and f['scope']=='owned-two-window-readonly-child-object-oracle')
 need(integer(f['pid']) and integer(i['target_pid'],f['pid']) and integer(i['owned_on_screen_windows'],0) and integer(f['own_on_screen_after_close'],0) and inventory['binary_sha256']==fixture['binary_sha256'])
 o=f['public_object_oracle'];need(o['finished'] is False and o['failure_reason']=='object_selector_unavailable' and o['main_thread'] is True and o['absence_policy_resolved'] is False and o['input_eligibility_qualified'] is False)
 need(o['collection_order']=='AXUIElement_then_public_objects' and o['limits']=={'nodes':32,'depth':5,'children':32,'role_units':128,'identifier_units':256} and all(type(x) is int for x in o['limits'].values()))
 nodes=o['nodes'];roots=o['roots'];need(type(nodes) is list and 1<=len(nodes)<=32 and type(roots) is list and len(roots)==1)
 docs={Path(root,n+'.xcodeproj').as_uri()+'/' for n in ['a','b']};r=roots[0];need(r['document'] in docs and r['declared_button_attached'] is True and integer(r['index'],0) and integer(r['native_window_id']) and r['native_window_id']>0 and integer(r['declared_button_window_id'],r['native_window_id']))
 found=[n for n in nodes if 'legacy_diagnostic' in n];need(len(found)==1 and found[0] is nodes[-1]);n=found[0];need(integer(n['index'],len(nodes)-1) and n['root_document']==r['document'] and integer(n['depth']) and 0<=n['depth']<=5 and integer(n['parent']) and -1<=n['parent']<n['index'])
 s=n['selectors'];need(all(type(s[k]) is bool for k in ['role','identifier','children']) and (s['role'] is False or s['children'] is False) and type(n['is_declared_NSButton']) is bool)
 d=n['legacy_diagnostic'];need(d['scope']=='missing-modern-selector-owned-object-only' and d['main_thread'] is True and type(d['is_declared_content_view']) is bool and d['absence_policy_resolved'] is False and d['input_eligibility_qualified'] is False)
 def text(v,cap):need(type(v) is str);v.encode('utf8');need(len(v.encode('utf-16-le'))//2<=cap)
 def string(v,cap):need(v['kind']=='string' and v['truncated'] is False);text(v['value'],cap);return v['value']
 def snapshot(v):
  need(type(v['names_selector']) is bool and type(v['value_selector']) is bool and v['getter_exception'] is False and 'failure' not in v)
  if not(v['names_selector'] and v['value_selector']):need('names' not in v and all(k not in v for k in ['AXRole','AXIdentifier','AXChildren']));return
  names=v['names'];need(type(names) is list and len(names)<=64)
  for name in names:text(name,128)
  for key,cap in [('AXRole',128),('AXIdentifier',256),('AXChildren',0)]:
   a=v[key]
   if key not in names:need(a=={'kind':'not_advertised'});continue
   if key=='AXChildren':need(a['kind'] in ['nil','array'] and integer(a['count']) and 0<=a['count']<=32);need(a['kind']!='nil' or a['count']==0)
   elif a['kind']=='nil':need(a=={'kind':'nil'})
   else:string(a,cap)
 snapshot(d['missing_object']);snapshot(d['declared_button']);need(string(d['declared_button_modern_role'],128)=='AXButton' and string(d['declared_button_modern_identifier'],256)=='owned-binding-button')
 return {'bounded_expected_rejection_diagnostic_admitted':True,'fixture_pid':f['pid'],'missing_object':d['missing_object'],'declared_button':d['declared_button'],'is_declared_content_view':d['is_declared_content_view'],'projection_crosscheck_admitted':False,'absence_policy_resolved':False,'native_input_qualified':False,'live_Xcode_route_qualified':False}
if __name__=='__main__':
 p=Path(__file__).parent;v=admitted(parsed((p/'fixture-record.json').read_text()),parsed((p/'inventory-record.json').read_text()),str(p/'owned-documents'));(p/'admission.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(v,sort_keys=True))
