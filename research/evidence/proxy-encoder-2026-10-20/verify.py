from pathlib import Path
import copy,json,sys
EXPECTED={'boardservices_uuid_verified':True,'activate_invoked':True,'activation_callbacks':1,'valid_after_activation':True,'valid_after_invalidate':False,'is_null_endpoint':False,'connection_class':'BSServiceInitiatingConnection','target_class':'BSXPCServiceConnectionProxy<FBSWorkspaceServiceServerInterface>','target_nil_after_activation':False,'scene_action_signature_arguments':6,'message_class':'BSXPCServiceConnectionMessage','action_invoked':True,'action_completion_callbacks':1,'owned_peer_connections':1,'invocation_received':1,'independent_xpc_equal':1}
def check(x,holdout):
 for k,v in EXPECTED.items():assert x[k]==v,(k,x[k],v)
 assert x['holdout']==holdout
 assert x['interposed_mach_calls']==len(x['trace'])<256
 assert x['interposed_mach_sends']==sum(bool(t['options']&1)for t in x['trace'])>0
 return True
def verify(w):
 receipts=[];n=0
 for mode,holdout in [('primary',False),('holdout',True)]:
  x=json.loads((w/(mode+'.json')).read_text());check(x,holdout);receipts.append({k:x[k]for k in EXPECTED})
  for k,v in EXPECTED.items():
   bad=copy.deepcopy(x);bad[k]=not v if isinstance(v,bool) else(v+1 if isinstance(v,int)else'mutated')
   try:check(bad,holdout)
   except AssertionError:n+=1
   else:raise AssertionError('accepted mutation '+k)
 return {'native_cases':2,'independent_whole_dictionary_equalities':2,'receipt_mutations_rejected':n,'receipts':receipts,'native_set_elements_tested':0,'native_mach_byte_parity':False,'actual_scene_execution':False,'target_settlement':False,'completion_means':'Owned SDK peer returned an empty reply; no scene execution or acknowledgement semantics inferred.'}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
