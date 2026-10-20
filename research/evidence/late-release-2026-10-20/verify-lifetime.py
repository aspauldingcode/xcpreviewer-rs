from pathlib import Path
import json,copy,hashlib,sys
REQUEST_HASH='3c74a86ed3501b3cbf6ee4fc2b6e933b199bf84ba49278ab8c21fec6601bfa78'
EMPTY=bytes.fromhex('435058400500000000f000000400000000000000')
def check(d,mode):
 pending=mode!='delivered';late=mode=='late-after-invalidate'
 expected={'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'independent_xpc_equal':1,'invocation_received':1,'valid_after_activation':True,'valid_after_invalidate':False,'withhold':pending,'late_reply':late,'action_completion_callbacks':1,'completion_on_owned_queue':1,'final_callback_wait':0,'final_token_wait':0,'token_drops_final':1,'token_marks':1,'callbacks_before_invalidate':0 if pending else 1,'token_drops_before_invalidate':0 if pending else 1,'callbacks_after_invalidate':0 if pending else 1,'token_drops_after_invalidate':0 if pending else 1,'callbacks_after_late':1 if late or not pending else 0,'token_drops_after_late':1 if late or not pending else 0,'observed_error_domain':'BSServiceConnectionErrorDomain'if mode=='withheld'else'','observed_error_code':3 if mode=='withheld'else 0}
 for k,v in expected.items():assert d[k]==v,(mode,k)
 reqs=[(i,r)for i,r in enumerate(d['trace'])if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex'])];assert len(reqs)==1
 i,r=reqs[0];body=bytes.fromhex(r['send_body_hex']);assert len(body)==312 and hashlib.sha256(body).hexdigest()==REQUEST_HASH
 assert r['api']==3 and r['complete']==1 and r['result']==0
 replies=[r for r in d['trace'][i+1:]if r['api']==3 and r['send_id']==0x20000000 and bytes.fromhex(r['send_body_hex']).startswith(b'CPX@')]
 assert len(replies)==(0 if mode=='withheld'else 1)
 for r in replies:assert r['complete']==1 and r['result']==0 and bytes.fromhex(r['send_body_hex'])==EMPTY
 return expected
if __name__=='__main__':
 folder=Path(sys.argv[1]);n=0;cases=[]
 for mode in ['delivered','withheld','late-after-invalidate']:
  d=json.load(open(folder/(mode+'.json')));expected=check(d,mode)
  for k,v in expected.items():
   bad=copy.deepcopy(d);bad[k]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else v+'!')
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted changed lifetime field '+k)
  cases.append({'mode':mode,'phase_expectations':expected,'request_body_bytes_equal':312,'reply_body_bytes_equal':0 if mode=='withheld'else 20})
 print(json.dumps({'cases':cases,'lifetime_receipt_mutants_rejected':n,'total_request_reply_bytes_verified':976,'target_operation_settlement':False,'all_native_resource_release_accounted':False,'scene_execution':False},indent=2))
