import json,copy,hashlib,unittest
from test_geometry import records,ROOT
from tree_admit import admitted,parsed

def encode(row,body,marker):
 raw=json.dumps(body)+'\n';row['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest(),stderr='owned_tree_pid:'+str(marker)+'\n')
def tree_records():
 f,i=records();v=json.loads(f['record']['stdout']);inv=json.loads(i['record']['stdout']);v.update(status='owned_tree_inventory_recorded',scope='owned-two-window-readonly-AX-tree')
 docs=[x['document'] for x in v['phases'][0]['rows']];limits={'nodes':32,'depth':5,'children':32,'attribute_names':64,'role_units':128,'identifier_units':256,'name_units':128};nodes=[];roots=[]
 for j,d in enumerate(docs):
  idx=j*2;roots.append({'index':idx,'document':d,'declared_native_window_id':41+j})
  for child in [False,True]:
   n={'index':idx+int(child),'parent':idx if child else -1,'root_document':d,'depth':int(child),'CF_type':134,'expected_AX_CF_type':134,'pid_error':0,'pid':123,'role':{'error':0,'CF_type':7,'value':'AXButton' if child else 'AXWindow','truncated':False},'identifier':{'error':0,'CF_type':7,'value':'owned-binding-button','truncated':False} if child else {'error':-25212,'CF_type':0},'children':{'error':-25212,'CF_type':0} if child else {'error':0,'CF_type':19,'count':1}}
   if child:n.update(terminal_status='NoValue',attribute_names={'error':0,'CF_type':19,'names':['AXRole','AXIdentifier','AXChildren'],'contains_AXChildren':True})
   nodes.append(n)
 v['tree_inventory']={'expected_string_CF_type':7,'expected_array_CF_type':19,'status':'owned_readonly_tree_inventory','enumeration_finished':True,'absence_policy_resolved':False,'input_eligibility_qualified':False,'AX_windows_error':0,'limits':limits,'nodes':nodes,'roots':roots}
 encode(f,v,123);encode(i,inv,124);return f,i
class TreeAdmissionTests(unittest.TestCase):
 def test_positive(self):self.assertTrue(admitted(*tree_records(),ROOT)['bounded_returned_status_inventory_admitted'])
 def test_semantic_faults(self):
  faults=['incomplete','claims_absence','claims_input','foreign_pid','wrong_type','pid_error','alias','cycle','parent_cycle','depth','node_limit','float_limit','role_type','role_truncated','identifier_error','children_error','missing_child','names_missing','names_bound','names_flag','terminal_mismatch','extra_button','missing_root','wrong_root_id','fixture_exit','undrained','timeout','cleanup']
  for fault in faults:
   f,i=tree_records();v=parsed(f['record']['stdout']);t=v['tree_inventory'];n=t['nodes']
   if fault=='incomplete':t['enumeration_finished']=False
   elif fault=='claims_absence':t['absence_policy_resolved']=True
   elif fault=='claims_input':t['input_eligibility_qualified']=True
   elif fault=='foreign_pid':n[1]['pid']=999
   elif fault=='wrong_type':n[1]['CF_type']=19
   elif fault=='pid_error':n[1]['pid_error']=-25204
   elif fault=='alias':n[1]['alias_to']=0
   elif fault=='cycle':n[1]['cycle']=True
   elif fault=='parent_cycle':n[1]['parent']=1
   elif fault=='depth':n[1]['depth']=6
   elif fault=='node_limit':
    for j in range(29):
     extra=copy.deepcopy(n[1 if j%2==0 else 3]);extra['index']=len(n);extra['role']['value']='AXImage';extra['identifier']={'error':-25212,'CF_type':0};n.append(extra)
    n[0]['children']['count']=16;n[2]['children']['count']=15
   elif fault=='float_limit':t['limits']['nodes']=32.0
   elif fault=='role_type':n[1]['role']['CF_type']=19
   elif fault=='role_truncated':n[1]['role']['truncated']=True
   elif fault=='identifier_error':n[1]['identifier']['error']=-25204
   elif fault=='children_error':n[1]['children']['error']=-25204
   elif fault=='missing_child':n[0]['children']['count']=2
   elif fault=='names_missing':del n[1]['attribute_names']
   elif fault=='names_bound':n[1]['attribute_names']['names']=['x'*129]
   elif fault=='names_flag':n[1]['attribute_names']['contains_AXChildren']=False
   elif fault=='terminal_mismatch':n[1]['terminal_status']='Unsupported'
   elif fault=='extra_button':
    extra=copy.deepcopy(n[3]);extra['index']=4;n.append(extra);n[2]['children']['count']=2
   elif fault=='missing_root':t['roots'].pop()
   elif fault=='wrong_root_id':t['roots'][0]['declared_native_window_id']=99
   elif fault=='fixture_exit':f['record']['report']['target_code']=78
   elif fault=='undrained':f['record']['report']['drained']=False
   elif fault=='timeout':v={'pid':123,'status':'owned_tree_deadline','admitted':False}
   else:
    z=parsed(i['record']['stdout']);z['owned_on_screen_windows']=1;encode(i,z,124)
   encode(f,v,123)
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
 def test_raw_faults(self):
  for fault in ['empty','invalid','hash','bytes','oversize','pid_disagreement','missing_marker','duplicate_marker','duplicate_key','nonfinite']:
   f,i=tree_records();r=f['record']
   if fault=='empty':r['stdout']=''
   elif fault=='invalid':r['stdout']='{'
   elif fault=='hash':r['stdoutSha256']='0'*64
   elif fault=='bytes':r['stdoutBytes']+=1
   elif fault=='oversize':
    z=parsed(r['stdout']);z['extra']=' '*131073;r['stdout']=json.dumps(z)
   elif fault=='pid_disagreement':r['stderr']='owned_tree_pid:999\n'
   elif fault=='missing_marker':r['stderr']=''
   elif fault=='duplicate_marker':r['stderr']*=2
   elif fault=='duplicate_key':r['stdout']=r['stdout'].replace('{','{"pid":999,',1)
   else:r['stdout']=r['stdout'].replace('123','NaN',1)
   if fault not in ['hash','bytes']:r['stdoutBytes']=len(r['stdout'].encode());r['stdoutSha256']=hashlib.sha256(r['stdout'].encode()).hexdigest()
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
if __name__=='__main__':unittest.main()
