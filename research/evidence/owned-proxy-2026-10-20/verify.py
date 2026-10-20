from pathlib import Path
import copy,json,sys
def check(x):
 expected={'mode':'configured','activate_invoked':True,'configured_interface':True,'connection_class':'BSServiceInitiatingConnection','endpoint_class':'BSServiceConnectionEndpoint','is_null_endpoint':True,'service':'owned.null.service','instance':'owned.null.instance','valid_before_activation':True,'valid_after_activation':False,'valid_after_invalidate':False,'target_nil_after_activation':True,'message_nil_after_activation':False,'message_class':'BSXPCServiceConnectionMessage','callback_same_connection':1,'callback_on_owned_queue':1,'invalidation_callbacks':1,'invalidate_invocations':2,'second_callback_wait_timed_out':1,'observation_window_ms':200,'scene_action_signature_arguments':0}
 for k,v in expected.items():assert x[k]==v,(k,x[k],v)
 assert x['interposed_mach_calls']==len(x['trace'])<256
 assert x['interposed_mach_sends']==sum(bool(t['options']&1)for t in x['trace'])>0
 return expected
def verify(folder):
 x=json.loads((folder/'configured.json').read_text());expected=check(x);n=0
 for k,v in expected.items():
  bad=copy.deepcopy(x);bad[k]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else 'mutated')
  try:check(bad)
  except AssertionError:n+=1
  else:raise AssertionError('accepted mutation '+k)
 return {'native_cases':1,'receipt_mutations_rejected':n,'observations':expected,'mach_calls':x['interposed_mach_calls'],'mach_sends':x['interposed_mach_sends'],'workspace_delivery':False,'settlement':False,'later_effects_excluded':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
