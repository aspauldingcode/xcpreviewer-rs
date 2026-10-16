import json,copy,unittest
from test_tree import tree_records,encode
from test_geometry import ROOT
from admit import admitted

def oracle_records():
 f,i=tree_records();v=json.loads(f['record']['stdout']);v.update(status='owned_child_object_oracle_recorded',scope='owned-two-window-readonly-child-object-oracle');nodes=[]
 for a in v['tree_inventory']['nodes']:
  child=a['role']['value']=='AXButton';n={k:a[k] for k in ['index','parent','root_document','depth']};n.update(is_declared_NSButton=child,selectors={'role':True,'identifier':True,'children':True},role={'kind':'string','value':a['role']['value'],'truncated':False},identifier={'kind':'string','value':'owned-binding-button','truncated':False} if child else {'kind':'nil'},children={'kind':'nil','count':0} if child else {'kind':'array','count':1});nodes.append(n)
 roots=[{'index':a['index'],'document':a['document'],'native_window_id':a['declared_native_window_id'],'declared_button_window_id':a['declared_native_window_id'],'declared_button_attached':True} for a in v['tree_inventory']['roots']]
 v['public_object_oracle']={'status':'owned_public_child_object_oracle','finished':True,'main_thread':True,'absence_policy_resolved':False,'input_eligibility_qualified':False,'collection_order':'AXUIElement_then_public_objects','limits':{'nodes':32,'depth':5,'children':32,'role_units':128,'identifier_units':256},'nodes':nodes,'roots':roots};encode(f,v,123);return f,i
class ObjectOracleTests(unittest.TestCase):
 def test_positive(self):self.assertTrue(admitted(*oracle_records(),ROOT)['owned_different_route_crosscheck_admitted'])
 def test_faults(self):
  for fault in ['unfinished','not_main','claims_absence','claims_input','wrong_window','detached','wrong_button_window','missing_pointer_match','false_pointer_match','pointer_role','parent','depth','alias','cycle','truncated','unavailable_children','nil_with_child','unmatched_role','wrong_order']:
   f,i=oracle_records();v=json.loads(f['record']['stdout']);o=v['public_object_oracle'];n=o['nodes']
   if fault=='unfinished':o['finished']=False
   elif fault=='not_main':o['main_thread']=False
   elif fault=='claims_absence':o['absence_policy_resolved']=True
   elif fault=='claims_input':o['input_eligibility_qualified']=True
   elif fault=='wrong_window':o['roots'][0]['native_window_id']=99
   elif fault=='detached':o['roots'][0]['declared_button_attached']=False
   elif fault=='wrong_button_window':o['roots'][0]['declared_button_window_id']=99
   elif fault=='missing_pointer_match':n[1]['is_declared_NSButton']=False
   elif fault=='false_pointer_match':n[0]['is_declared_NSButton']=True
   elif fault=='pointer_role':n[1]['role']['value']='AXImage'
   elif fault=='parent':n[1]['parent']=1
   elif fault=='depth':n[1]['depth']=6
   elif fault=='alias':n[1]['alias_to']=0
   elif fault=='cycle':n[1]['cycle']=True
   elif fault=='truncated':n[1]['role']['truncated']=True
   elif fault=='unavailable_children':n[1]['selectors']['children']=False
   elif fault=='nil_with_child':n[0]['children']['kind']='nil'
   elif fault=='unmatched_role':n[1]['role']['value']='AXUnknown'
   else:o['collection_order']='simultaneous'
   encode(f,v,123)
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
if __name__=='__main__':unittest.main()
