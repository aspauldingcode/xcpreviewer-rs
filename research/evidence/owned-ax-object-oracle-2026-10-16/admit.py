"""Different-route owned observation cross-check; not an absence or input policy."""
import copy,json,hashlib
from collections import Counter
from pathlib import Path
from tree_admit import receipt,admitted as tree_admitted,need,integer,parsed

def admitted(fixture,inventory,root):
 f=receipt(fixture);need(f['status']=='owned_child_object_oracle_recorded' and f['scope']=='owned-two-window-readonly-child-object-oracle' and f['admitted'] is True)
 # Raw native output is verified first; this internal adapted receipt only reuses the prior tree validator.
 g=copy.deepcopy(fixture);v=copy.deepcopy(f);v.update(status='owned_tree_inventory_recorded',scope='owned-two-window-readonly-AX-tree');raw=json.dumps(v);g['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest());tree_admitted(g,inventory,root)
 o=f['public_object_oracle'];need(o['status']=='owned_public_child_object_oracle' and o['finished'] is True and o['main_thread'] is True and o['absence_policy_resolved'] is False and o['input_eligibility_qualified'] is False and o['collection_order']=='AXUIElement_then_public_objects' and 'failure_reason' not in o)
 limits={'nodes':32,'depth':5,'children':32,'role_units':128,'identifier_units':256};need(o['limits']==limits and all(type(x) is int for x in o['limits'].values()))
 nodes=o['nodes'];roots=o['roots'];need(type(nodes) is list and 2<=len(nodes)<=32 and type(roots) is list and len(roots)==2)
 ids={x['document']:x['declared_native_window_id'] for x in f['tree_inventory']['roots']};need({x['document'] for x in roots}==set(ids));rootmap={x['index']:x for x in roots};need(len(rootmap)==2)
 for x in roots:need(integer(x['index']) and 0<=x['index']<len(nodes) and integer(x['native_window_id'],ids[x['document']]) and integer(x['declared_button_window_id'],ids[x['document']]) and x['declared_button_attached'] is True)
 def string(v,cap):need(type(v) is str);v.encode('utf8');need(len(v.encode('utf-16-le'))//2<=cap)
 def value(a,cap):need(a['kind']=='string' and a['truncated'] is False);string(a['value'],cap);return a['value']
 known={d:0 for d in ids};signatures={d:[] for d in ids};pairs=[]
 for idx,n in enumerate(nodes):
  need(integer(n['index'],idx) and integer(n['parent']) and integer(n['depth']) and 0<=n['depth']<=5 and n['root_document'] in ids and 'alias_to' not in n and 'cycle' not in n)
  selectors=n['selectors'];need(selectors['role'] is True and selectors['children'] is True and type(selectors['identifier']) is bool)
  role=value(n['role'],128);identifier=n['identifier'];kind=identifier['kind']
  if kind=='string':need(selectors['identifier'] is True);ident=value(identifier,256)
  else:need(kind in ['nil','selector_unavailable'] and ((kind=='nil' and selectors['identifier'] is True) or (kind=='selector_unavailable' and selectors['identifier'] is False)));ident=None
  if n['parent']==-1:need(idx in rootmap and rootmap[idx]['document']==n['root_document'] and n['depth']==0 and role=='AXWindow')
  else:need(0<=n['parent']<idx);p=nodes[n['parent']];need(n['depth']==p['depth']+1 and n['root_document']==p['root_document'])
  children=n['children'];need(children['kind'] in ['nil','array'] and integer(children['count']) and 0<=children['count']<=32);direct=[x for x in nodes if x['parent']==idx];need(len(direct)==children['count'])
  if children['kind']=='nil':need(integer(children['count'],0))
  need(type(n['is_declared_NSButton']) is bool)
  if n['is_declared_NSButton']:need(role=='AXButton' and ident=='owned-binding-button');known[n['root_document']]+=1
  if role=='AXButton' and ident=='owned-binding-button':need(n['is_declared_NSButton'] is True)
  signatures[n['root_document']].append((role,ident))
  matches=[x for x in f['tree_inventory']['nodes'] if x['root_document']==n['root_document'] and x['role']['value']==role and x['identifier'].get('value')==ident];need(len(matches)==1);a=matches[0];c=a['children'];axcount=c['count'] if c['error']==0 else 0;need(children['count']==axcount)
  pairs.append({'document':n['root_document'],'role':role,'public_children_kind':children['kind'],'public_children_count':children['count'],'AX_children_error':c['error']})
 need(set(rootmap)=={i for i,n in enumerate(nodes) if n['parent']==-1} and all(v==1 for v in known.values()))
 for d in ids:need(Counter(signatures[d])==Counter((x['role']['value'],x['identifier'].get('value')) for x in f['tree_inventory']['nodes'] if x['root_document']==d))
 return {'owned_different_route_crosscheck_admitted':True,'declared_NSButton_pointer_matches':known,'observed_child_pairs':pairs,'same_producer':True,'simultaneous_snapshot':False,'absence_policy_resolved':False,'native_input_qualified':False,'live_Xcode_route_qualified':False}
if __name__=='__main__':
 p=Path(__file__).parent;v=admitted(parsed((p/'fixture-record.json').read_text()),parsed((p/'inventory-record.json').read_text()),str(p/'owned-documents'));(p/'admission.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(v,sort_keys=True))
