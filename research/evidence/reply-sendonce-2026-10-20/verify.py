from pathlib import Path
import json,copy,sys,importlib.util
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('verify-rights.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def check_right(before,after):
 assert before=={'refs':1,'refs_status':0,'type':262144,'type_status':0}
 assert after['refs_status']==15 and after['type_status']==15
 # On failed queries output buffers carry no semantic count/type evidence.
def check(d,mode):
 a=prior.check(d,mode);selected=[r for r in d['trace']if r['reply_selected']]
 assert len(selected)==(0 if mode=='withheld'else 1)
 for r in selected:
  assert r['reply_selected']==1 and r['api']==3 and r['complete']==1 and r['result']==0
  assert r['reply_remote_name']==r['reply_header_remote_name'] and r['reply_remote_name']>0 and r['reply_remote_name']!=a
  assert r['reply_receive_name']==a and r['reply_disposition']==18
  check_right(r['reply_before'],r['reply_after'])
 releases=d['release_trace'];assert d['abandon_wrapper_calls']==(1 if mode=='withheld'else 0)
 assert len(releases)==(1 if mode=='withheld'else 0)
 for r in releases:
  assert r['api']==1 and r['result']==0 and r['receive_name']==a and r['name']>0 and r['name']!=a
  check_right(r['before'],r['after'])
 return selected,releases
if __name__=='__main__':
 folder=Path(sys.argv[1]);n=0;bodies=0;cases=[]
 for mode in ['delivered','withheld','late-after-invalidate']:
  d=json.load(open(folder/(mode+'.json')));selected,releases=check(d,mode)
  def reject(bad):
   global n
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted corrupt send-once evidence')
  for i,r in enumerate(d['trace']):
   if r['reply_selected']:
    for key in ['reply_selected','reply_remote_name','reply_header_remote_name','reply_receive_name','reply_disposition','result','complete']:
     bad=copy.deepcopy(d);bad['trace'][i][key]+=1;reject(bad)
    for phase in ['reply_before','reply_after']:
     for key in (['refs','refs_status','type','type_status']if phase=='reply_before'else['refs_status','type_status']):
      bad=copy.deepcopy(d);bad['trace'][i][phase][key]+=1;reject(bad)
  bad=copy.deepcopy(d);bad['abandon_wrapper_calls']+=1;reject(bad)
  for j,r in enumerate(releases):
   for key in ['api','result','receive_name']:
    bad=copy.deepcopy(d);bad['release_trace'][j][key]+=1;reject(bad)
   for phase in ['before','after']:
    for key in (['refs','refs_status','type','type_status']if phase=='before'else['refs_status','type_status']):
     bad=copy.deepcopy(d);bad['release_trace'][j][phase][key]+=1;reject(bad)
   bad=copy.deepcopy(d);bad['release_trace'][j]['name']=d['rights_before']['name'];reject(bad)
  for i,r in enumerate(d['trace']):
   body=bytes.fromhex(r['send_body_hex'])
   if b'sceneID:sendActions:'in body or r['reply_selected']:
    for offset in range(len(body)):
     changed=bytearray(body);changed[offset]^=1;bad=copy.deepcopy(d);bad['trace'][i]['send_body_hex']=changed.hex();reject(bad);bodies+=1
  cases.append({'mode':mode,'send_observations':len(selected),'explicit_abandon_deallocate_observations':len(releases),'distinct_receive_and_send_once_names':True,'send_once_refs_before':1,'exact_send_once_name_invalid_after':True})
 print(json.dumps({'cases':cases,'corrupt_evidence_rejected':n,'body_byte_mutations_rejected':bodies,'request_reply_bytes_verified':976,'source_disposition_MOVE_SEND_ONCE':18,'native_SEND_ONCE_type':262144,'failed_output_values_ignored':True,'all_native_resource_release_accounted':False,'target_operation_settlement':False,'global_port_object_destruction':False},indent=2))
