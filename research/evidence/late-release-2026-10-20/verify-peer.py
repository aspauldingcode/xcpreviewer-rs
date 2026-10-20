from pathlib import Path
import json,copy,sys,hashlib,importlib.util
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('verify-rights.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
HASH='3c74a86ed3501b3cbf6ee4fc2b6e933b199bf84ba49278ab8c21fec6601bfa78'
def check(d,mode):
 peer=mode!='withheld';late=mode=='peer-loss-late'
 assert d['factory_hits']==1 and d['factory_restored'] is True and d['factory_types']=='@40@0:8@16q24@32'
 assert d['factory_user_info']=={'BSErrorCodeDescription':'OperationFailed','NSLocalizedFailureReason':'XPC error received on message reply handler'}
 offsets=[x['offset']for x in d['factory_stack']if x['image']=='/System/Library/PrivateFrameworks/BoardServices.framework/Versions/A/BoardServices'];assert offsets[:3]==[432180,431340,363308]
 if not peer:prior.check(d,'withheld')
 expected={'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'independent_xpc_equal':1,'invocation_received':1,'valid_after_activation':True,'valid_after_invalidate':False,'withhold':True,'late_reply':late,'peer_cancel_requested':peer,'peer_cancel_events':1,'peer_cancel_wait':0,'callbacks_after_peer_cancel':int(peer),'token_drops_after_peer_cancel':int(peer),'action_completion_callbacks':1,'completion_on_owned_queue':1,'final_callback_wait':0,'final_token_wait':0,'token_drops_final':1,'token_marks':1,'callbacks_before_invalidate':int(peer),'token_drops_before_invalidate':int(peer),'callbacks_after_invalidate':int(peer),'token_drops_after_invalidate':int(peer),'callbacks_after_late':int(peer),'token_drops_after_late':int(peer),'observed_error_domain':'BSServiceConnectionErrorDomain','observed_error_code':3,'abandon_wrapper_calls':0 if late else 1}
 for k,v in expected.items():assert d[k]==v,(mode,k)
 reqs=[r for r in d['trace']if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex'])];assert len(reqs)==1
 r=reqs[0];body=bytes.fromhex(r['send_body_hex']);assert len(body)==312 and hashlib.sha256(body).hexdigest()==HASH and r['result']==0 and r['complete']==1 and r['api']==3
 assert not any(r['reply_selected']for r in d['trace'])
 # No selected reply send is claimed; SDK late-send attempt is not a kernel send receipt.
 a=d['rights_before']['name'];assert a>0
 phases=['rights_before','rights_after','rights_late','rights_final']+(['rights_peer']if peer else [])
 for phase in phases:
  q=d[phase];assert q['name']==a and q['header_name']==a and(q['header_bits']>>8)&255==21
  live=phase=='rights_before' or(not peer and phase in ['rights_after','rights_late'])
  assert q['type_status']==(0 if live else 15)
  for kind in ['receive','send','send_once','dead_name']:
   assert q[kind]['status']==(0 if live else 15)
   if live:assert q[kind]['refs']==int(kind=='receive')
  assert q['receive_status']['status']==(0 if live else 15)
  if live:assert q['type']==131072 and q['receive_status']=={'status':0,'count':10,'send_once_rights':1,'send_rights_present':0,'queued_messages':0,'sequence_number':0}
 releases=d['release_trace'];assert len(releases)==(0 if late else 1)
 for r in releases:
  assert r['api']==1 and r['result']==0 and r['name']>0 and r['name']!=a and r['receive_name']==a
  assert r['before']=={'type_status':0,'type':1048576 if peer else 262144,'refs_status':0,'refs':0 if peer else 1}
  assert r['dead_before_status']==0 and r['dead_before_refs']==int(peer)
  assert r['after']['type_status']==15 and r['after']['refs_status']==15 and r['dead_after_status']==15
 return expected
if __name__=='__main__':
 folder=Path(sys.argv[1]);n=0;bytes_checked=0;cases=[]
 for mode in ['withheld','peer-loss-withheld','peer-loss-late']:
  d=json.load(open(folder/(mode+'.json')));expected=check(d,mode)
  def reject(bad):
   global n
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted corrupt peer-loss evidence')
  for k,v in expected.items():
   bad=copy.deepcopy(d);bad[k]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else v+'!');reject(bad)
  for key,value in [('factory_hits',2),('factory_restored',False),('factory_types','incorrect'),('factory_user_info',{}),('factory_stack',[])]:
   bad=copy.deepcopy(d);bad[key]=value;reject(bad)
  for j in range(3):
   bad=copy.deepcopy(d);indices=[i for i,x in enumerate(bad['factory_stack'])if x['image']=='/System/Library/PrivateFrameworks/BoardServices.framework/Versions/A/BoardServices'];bad['factory_stack'][indices[j]]['offset']+=4;reject(bad)
  for phase in ['rights_before','rights_after','rights_late','rights_final']+(['rights_peer']if mode!='withheld'else []):
   q=d[phase]
   for key in ['name','header_name','header_bits','type_status']+(['type']if q['type_status']==0 else []):
    bad=copy.deepcopy(d);bad[phase][key]+=256 if key=='header_bits'else 1;reject(bad)
   for kind in ['receive','send','send_once','dead_name']:
    for key in ['status']+(['refs']if q[kind]['status']==0 else []):
     bad=copy.deepcopy(d);bad[phase][kind][key]+=1;reject(bad)
   for key in ['status']+(['count','send_once_rights','send_rights_present','queued_messages','sequence_number']if q['receive_status']['status']==0 else []):
    bad=copy.deepcopy(d);bad[phase]['receive_status'][key]+=1;reject(bad)
  for j,r in enumerate(d['release_trace']):
   for key in ['api','result','receive_name','dead_before_status','dead_before_refs','dead_after_status']:
    bad=copy.deepcopy(d);bad['release_trace'][j][key]+=1;reject(bad)
   bad=copy.deepcopy(d);bad['release_trace'][j]['name']=d['rights_before']['name'];reject(bad)
   for phase in ['before','after']:
    for key in ['type_status','refs_status']+(['type','refs']if phase=='before'else []):
     bad=copy.deepcopy(d);bad['release_trace'][j][phase][key]+=1;reject(bad)
  for i,r in enumerate(d['trace']):
   body=bytes.fromhex(r['send_body_hex'])
   if b'sceneID:sendActions:'in body:
    for offset in range(len(body)):
     b=bytearray(body);b[offset]^=1;bad=copy.deepcopy(d);bad['trace'][i]['send_body_hex']=b.hex();reject(bad);bytes_checked+=1
  cases.append({'mode':mode,'completion_before_explicit_invalidation':mode!='withheld','error_code':3,'exact_receive_name_invalid_after_peer_cancel':mode!='withheld','release_observed':bool(d['release_trace']),'reply_right_before_explicit_release':'unobserved'if mode=='peer-loss-late'else('dead-name'if mode!='withheld'else'send-once'),'selected_kernel_reply_sends':0})
 print(json.dumps({'cases':cases,'corrupt_evidence_rejected':n,'request_body_bytes_verified':bytes_checked,'fresh_kernel_reply_body_bytes':0,'all_native_resource_release_accounted':False,'target_operation_settlement':False,'global_port_object_destruction':False,'late_SDK_send_attempt_is_not_kernel_send':True,'native_error_factory_source_offsets':[432180,431340,363308],'native_error_factory_restored':True},indent=2))
