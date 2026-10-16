import copy,json,unittest
from test_tree import tree_records,encode
from test_geometry import ROOT
from admit import admitted

def records():
 f,i=tree_records();f['binary_sha256']='a'*64;i['binary_sha256']='a'*64;v=json.loads(f['record']['stdout']);doc=v['tree_inventory']['roots'][0]['document'];wid=v['tree_inventory']['roots'][0]['declared_native_window_id']
 snap={'names_selector':True,'value_selector':True,'getter_exception':False,'names':['AXRole','AXChildren'],'AXRole':{'kind':'string','value':'AXStaticText','truncated':False},'AXIdentifier':{'kind':'not_advertised'},'AXChildren':{'kind':'array','count':0}}
 d={'scope':'missing-modern-selector-owned-object-only','main_thread':True,'is_declared_content_view':False,'absence_policy_resolved':False,'input_eligibility_qualified':False,'missing_object':copy.deepcopy(snap),'declared_button':copy.deepcopy(snap),'declared_button_modern_role':{'kind':'string','value':'AXButton','truncated':False},'declared_button_modern_identifier':{'kind':'string','value':'owned-binding-button','truncated':False}}
 v.update(status='owned_fixture_rejected',admitted=False,scope='owned-two-window-readonly-child-object-oracle',public_object_oracle={'finished':False,'failure_reason':'object_selector_unavailable','main_thread':True,'absence_policy_resolved':False,'input_eligibility_qualified':False,'collection_order':'AXUIElement_then_public_objects','limits':{'nodes':32,'depth':5,'children':32,'role_units':128,'identifier_units':256},'roots':[{'document':doc,'index':0,'declared_button_attached':True,'native_window_id':wid,'declared_button_window_id':wid}],'nodes':[{'index':0,'parent':-1,'depth':0,'root_document':doc,'selectors':{'role':False,'children':False,'identifier':False},'is_declared_NSButton':False,'legacy_diagnostic':d}]})
 encode(f,v,123);f['error']='Error: Observed compiler failed: 78';f['record']['report']['target_code']=78;return f,i
class DiagnosticTests(unittest.TestCase):
 def test_supported_and_unavailable(self):
  for available in [True,False]:
   f,i=records();v=json.loads(f['record']['stdout'])
   if not available:v['public_object_oracle']['nodes'][0]['legacy_diagnostic']['missing_object']={'names_selector':False,'value_selector':False,'getter_exception':False};encode(f,v,123)
   self.assertTrue(admitted(f,i,ROOT)['bounded_expected_rejection_diagnostic_admitted'])
 def test_faults(self):
  for fault in ['exit','error','hash','bytes','pid','drain','remaining','inventory','binary','both_invalid_binary','close','claimed_projection','claimed_absence','claimed_input','finished','reason','modern_available','namecap','nametype','truncated','exception','failure','advertised_mismatch','nilcount','childcap','boolcount','wrong_marker','duplicate_diagnostic','foreign_doc']:
   f,i=records();v=json.loads(f['record']['stdout']);o=v['public_object_oracle'];n=o['nodes'][0];d=n['legacy_diagnostic'];s=d['missing_object']
   if fault=='exit':f['record']['report']['target_code']=0
   elif fault=='error':f['error']=None
   elif fault=='hash':f['record']['stdoutSha256']='0'*64
   elif fault=='bytes':f['record']['stdoutBytes']+=1
   elif fault=='pid':i['record']['stdout']='{"target_pid":999,"owned_on_screen_windows":0}'
   elif fault=='drain':f['record']['report']['drained']=False
   elif fault=='remaining':f['record']['report']['remaining_observed']=1
   elif fault=='inventory':i['record']['report']['target_code']=78
   elif fault=='binary':i['binary_sha256']='other'
   elif fault=='both_invalid_binary':i['binary_sha256']=f['binary_sha256']=None
   elif fault=='close':v['own_on_screen_after_close']=1
   elif fault=='claimed_projection':v['admitted']=True
   elif fault=='claimed_absence':d['absence_policy_resolved']=True
   elif fault=='claimed_input':d['input_eligibility_qualified']=True
   elif fault=='finished':o['finished']=True
   elif fault=='reason':o['failure_reason']='other'
   elif fault=='modern_available':n['selectors'].update(role=True,children=True)
   elif fault=='namecap':s['names']=['x']*65
   elif fault=='nametype':s['names']=[4]
   elif fault=='truncated':s['AXRole']['truncated']=True
   elif fault=='exception':s['getter_exception']=True
   elif fault=='failure':s['failure']='bad'
   elif fault=='advertised_mismatch':s['AXIdentifier']={'kind':'nil'}
   elif fault=='nilcount':s['AXChildren']={'kind':'nil','count':1}
   elif fault=='childcap':s['AXChildren']['count']=33
   elif fault=='boolcount':s['AXChildren']['count']=False
   elif fault=='wrong_marker':d['declared_button_modern_identifier']['value']='wrong'
   elif fault=='duplicate_diagnostic':o['nodes'].append(copy.deepcopy(n))
   else:o['roots'][0]['document']='file:///foreign/'
   if fault not in ['hash','bytes','pid']:encode(f,v,123)
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
if __name__=='__main__':unittest.main()
