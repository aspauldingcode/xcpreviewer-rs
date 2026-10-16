import copy,json,unittest
from admit import admitted
ROOT='/private/tmp/owned-binding-test'
def records():
 docs=['file://'+ROOT+'/'+x+'.xcodeproj/' for x in ['a','b']]
 phases=[]
 for n in range(3):
  phases.append({'status':'observed','own_cg_windows':2,'rows':[{'document':d,'button_ancestor_matches':True,'fixture_window_id':41+i,'candidate_ids':[41+i] if n<2 else [41,42],'unique_candidate_equals_fixture':n<2} for i,d in enumerate(docs)]})
 f={'pid':123,'admitted':True,'status':'owned_geometry_correlation_admitted','own_on_screen_after_close':0,'phases':phases}
 def wrap(v):return {'error':None,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stdout':json.dumps(v)}}
 return wrap(f),wrap({'target_pid':123,'owned_on_screen_windows':0})
class AdmissionTests(unittest.TestCase):
 def test_complete_owned_synthetic(self):
  self.assertTrue(admitted(*records(),ROOT)['owned_fixture_admitted'])
 def test_combined_cleanup_and_phase_faults(self):
  for fault in ['leftover','null_inventory','wrong_pid','inventory_exit','fixture_exit','undrained','deadline','wrong_button','missing_doc','wrong_id','no_ambiguity','claimed_reject']:
   f,i=records();a=json.loads(f['record']['stdout']);b=json.loads(i['record']['stdout'])
   if fault=='leftover':b['owned_on_screen_windows']=1
   elif fault=='null_inventory':b['owned_on_screen_windows']=-1
   elif fault=='wrong_pid':b['target_pid']=124
   elif fault=='inventory_exit':i['record']['report']['target_code']=1
   elif fault=='fixture_exit':f['record']['report']['target_code']=78
   elif fault=='undrained':f['record']['report']['drained']=False
   elif fault=='deadline':a['phases'][1]={'status':'owned_phase_deadline'}
   elif fault=='wrong_button':a['phases'][0]['rows'][0]['button_ancestor_matches']=False
   elif fault=='missing_doc':a['phases'][0]['rows'][0]['document']='file:///other'
   elif fault=='wrong_id':a['phases'][1]['rows'][0]['fixture_window_id']=99
   elif fault=='no_ambiguity':a['phases'][2]['rows'][0]['candidate_ids']=[41]
   else:a['admitted']=False
   f['record']['stdout']=json.dumps(a);i['record']['stdout']=json.dumps(b)
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
if __name__=='__main__':unittest.main()
