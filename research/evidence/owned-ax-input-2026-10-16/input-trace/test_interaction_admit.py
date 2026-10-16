import copy,json,unittest
from test_admit import records,ROOT
from admit import admitted

def action_records():
 f,i=records();v=json.loads(f['record']['stdout']);v['status']='owned_interaction_control_admitted';v['scope']='owned-two-window-AXPress-interaction';doc='file://'+ROOT+'/b.xcodeproj/'
 good={'accepted':True,'reason':'validated','document':doc,'native_window_id':42,'AXPress_available':True,'AX_action_names_error':0,'AX_action_name_count':1}
 def counts(n):return {'a':0,'b':n,'unknown':0}
 v['interaction_steps']=[{'kind':'selection','validation':good,'counts':counts(0)},{'kind':'positive','result':{'action_attempted':True,'AX_press_error':0,'validation':good},'counts':counts(1)},{'kind':'stale','result':{'action_attempted':False,'validation':{'accepted':False,'reason':'binding_changed'}},'counts':counts(1)},{'kind':'overlap','result':{'action_attempted':False,'validation':{'accepted':False,'reason':'CG_identity_not_unique','candidates':[42,41]}},'counts':counts(1)}];v['callback_counts']=counts(1);f['record']['stdout']=json.dumps(v);return f,i
class InteractionAdmissionTests(unittest.TestCase):
 def test_positive(self):self.assertTrue(admitted(*action_records(),ROOT)['owned_AXPress_callback_control_observed'])
 def test_faults(self):
  for fault in ['wrong_target','wrong_id','missing_error','bool_error','action_missing','stale_action','overlap_action','other_callback','no_callback','extra_callback','wrong_reason','duplicate_candidates','no_action_available','action_names_error','fixture_exit','undrained','cleanup_leftover']:
   f,i=action_records();v=json.loads(f['record']['stdout']);s=v['interaction_steps']
   if fault=='wrong_target':s[0]['validation']['document']='file:///other'
   elif fault=='wrong_id':s[0]['validation']['native_window_id']=99
   elif fault=='missing_error':del s[1]['result']['AX_press_error']
   elif fault=='bool_error':s[1]['result']['AX_press_error']=False
   elif fault=='action_missing':s[1]['result']['action_attempted']=False
   elif fault=='stale_action':s[2]['result']['action_attempted']=True
   elif fault=='overlap_action':s[3]['result']['action_attempted']=True
   elif fault=='other_callback':v['callback_counts']={'a':1,'b':0,'unknown':0}
   elif fault=='no_callback':s[1]['counts']['b']=0
   elif fault=='extra_callback':s[2]['counts']['b']=2
   elif fault=='wrong_reason':s[2]['result']['validation']['reason']='validated'
   elif fault=='duplicate_candidates':s[3]['result']['validation']['candidates']=[42,42]
   elif fault=='no_action_available':s[0]['validation']['AXPress_available']=False
   elif fault=='action_names_error':s[1]['result']['validation']['AX_action_names_error']=-25205
   elif fault=='fixture_exit':f['record']['report']['target_code']=78
   elif fault=='undrained':f['record']['report']['drained']=False
   else:
    z=json.loads(i['record']['stdout']);z['owned_on_screen_windows']=1;i['record']['stdout']=json.dumps(z)
   f['record']['stdout']=json.dumps(v)
   with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):admitted(f,i,ROOT)
if __name__=='__main__':unittest.main()
