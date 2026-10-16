"""Frozen research receipt gate; terminal statuses do not establish subtree absence."""
import copy,hashlib,json,re
from pathlib import Path
from geometry_admit import admitted as geometry_admitted

def need(v):
 if not v:raise ValueError('Owned tree admission rejected')
def integer(v,n=None):return type(v) is int and (n is None or v==n)
def parsed(text):
 def pairs(items):
  out={}
  for k,v in items:
   need(k not in out);out[k]=v
  return out
 def bad(v):raise ValueError('Nonfinite JSON')
 return json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
def receipt(row):
 r=row['record'];p=r['report'];need(row['error'] is None and integer(p['target_code'],0) and p['failure'] is None and p['drained'] is True and integer(p['remaining_observed'],0) and r['emergencyClosed'] is False and r['privateAbortRequested'] is False)
 raw=r['stdout'].encode('utf-8');need(len(raw)<=131072 and integer(r['stdoutBytes'],len(raw)) and r['stdoutSha256']==hashlib.sha256(raw).hexdigest())
 markers=re.findall(r'^owned_tree_pid:([1-9][0-9]*)$',r['stderr'],re.M);need(len(markers)==1 and 1<int(markers[0])<=2147483647)
 v=parsed(r['stdout']);need(type(v) is dict)
 if 'pid' in v:need(integer(v['pid'],int(markers[0])))
 return v

def admitted(fixture,inventory,root):
 f=receipt(fixture);i=receipt(inventory);need(f['status']=='owned_tree_inventory_recorded' and f['scope']=='owned-two-window-readonly-AX-tree' and f['admitted'] is True)
 # Reuse geometry checks via explicit internal status adaptation, after raw-byte admission.
 g=copy.deepcopy(fixture);v=copy.deepcopy(f);v['status']='owned_geometry_correlation_admitted';g['record']['stdout']=json.dumps(v);geometry_admitted(g,inventory,root)
 t=f['tree_inventory'];need(t['status']=='owned_readonly_tree_inventory' and t['enumeration_finished'] is True and t['absence_policy_resolved'] is False and t['input_eligibility_qualified'] is False and 'failure_reason' not in t)
 limits={'nodes':32,'depth':5,'children':32,'attribute_names':64,'role_units':128,'identifier_units':256,'name_units':128};need(t['limits']==limits and all(type(x) is int for x in t['limits'].values()) and integer(t['AX_windows_error'],0))
 st=t['expected_string_CF_type'];at=t['expected_array_CF_type'];need(integer(st) and st>0 and integer(at) and at>0)
 nodes=t['nodes'];roots=t['roots'];need(type(nodes) is list and 2<=len(nodes)<=32 and type(roots) is list and len(roots)==2)
 docs={Path(root,n+'.xcodeproj').as_uri()+'/' for n in ['a','b']};ids={a['document']:a['fixture_window_id'] for a in f['phases'][0]['rows']};need({a['document'] for a in roots}==docs)
 rootmap={a['index']:a for a in roots};need(len(rootmap)==2)
 for a in roots:need(integer(a['index']) and 0<=a['index']<len(nodes) and integer(a['declared_native_window_id'],ids[a['document']]))
 def string(v,cap):
  need(type(v) is str);v.encode('utf-8');need(len(v.encode('utf-16-le'))//2<=cap)
 def value(a,cap):need(integer(a['error'],0) and integer(a['CF_type'],st) and a['truncated'] is False);string(a['value'],cap);return a['value']
 observed={d:0 for d in docs};terminal=[]
 for idx,n in enumerate(nodes):
  need(integer(n['index'],idx) and integer(n['parent']) and integer(n['depth']) and 0<=n['depth']<=5 and n['root_document'] in docs and 'alias_to' not in n and 'cycle' not in n)
  need(integer(n['expected_AX_CF_type']) and n['expected_AX_CF_type']>0 and integer(n['CF_type'],n['expected_AX_CF_type']) and integer(n['pid_error'],0) and integer(n['pid'],f['pid']))
  role=value(n['role'],128);identifier=n['identifier'];ie=identifier['error'];need(integer(ie))
  if ie==0:ident=value(identifier,256)
  else:need(ie in [-25205,-25212] and integer(identifier['CF_type'],0) and 'value' not in identifier and 'truncated' not in identifier);ident=None
  if n['parent']==-1:need(idx in rootmap and rootmap[idx]['document']==n['root_document'] and n['depth']==0 and role=='AXWindow')
  else:
   need(0<=n['parent']<idx);parent=nodes[n['parent']];need(n['depth']==parent['depth']+1 and n['root_document']==parent['root_document'])
  c=n['children'];ce=c['error'];need(integer(ce));direct=[x for x in nodes if x['parent']==idx]
  if ce==0:need(integer(c['CF_type'],at) and integer(c['count']) and 0<=c['count']<=32 and len(direct)==c['count'] and 'terminal_status' not in n and 'attribute_names' not in n)
  else:
   need(ce in [-25205,-25212] and integer(c['CF_type'],0) and not direct and n['terminal_status']==('NoValue' if ce==-25212 else 'Unsupported'))
   a=n['attribute_names'];names=a['names'];need(integer(a['error'],0) and integer(a['CF_type'],at) and type(names) is list and len(names)<=64)
   for name in names:string(name,128)
   need(type(a['contains_AXChildren']) is bool and a['contains_AXChildren']==('AXChildren' in names));terminal.append({'role':role,'error':ce,'contains_AXChildren':a['contains_AXChildren']})
  if role=='AXButton' and ident=='owned-binding-button':observed[n['root_document']]+=1
 need(set(rootmap)=={j for j,n in enumerate(nodes) if n['parent']==-1} and all(x==1 for x in observed.values()))
 return {'bounded_returned_status_inventory_admitted':True,'nodes':len(nodes),'observed_declared_buttons':observed,'terminal_statuses':terminal,'absence_policy_resolved':False,'native_input_qualified':False,'live_Xcode_route_qualified':False}
if __name__=='__main__':
 p=Path(__file__).parent;v=admitted(parsed((p/'fixture-record.json').read_text()),parsed((p/'inventory-record.json').read_text()),str(p/'owned-documents'));(p/'admission.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
