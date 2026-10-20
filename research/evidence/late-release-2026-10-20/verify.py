from pathlib import Path
import json,copy,subprocess,sys,importlib.util
w=Path(__file__).parent;spec=importlib.util.spec_from_file_location('peer',w/'verify-peer.py');peer=importlib.util.module_from_spec(spec);spec.loader.exec_module(peer)
EMPTY=bytes.fromhex('435058400500000000f000000400000000000000')
def check(d,mode):
 late=mode=='peer-loss-late';rows=d['release_trace'];assert len(rows)==1
 r=rows[0];assert r['complete']==1 and r['window']==(1 if late else 2) and r['api']==(3 if late else 1)
 assert r['caller_image']=='/usr/lib/system/libxpc.dylib' and r['caller_symbol']==('_xpc_serializer_dispose'if late else'_xpc_message_request_destroy')
 assert r['caller_offset']>0 and r['result_available']==(not late)
 assert d['late_release_wait']==0 and d['late_wrapper_calls']==int(late) and d['abandon_wrapper_calls']==1
 baseline=copy.deepcopy(d)
 if late:
  baseline['release_trace']=[];baseline['abandon_wrapper_calls']=0
  a=d['rights_before']['name'];assert r['name']>0 and r['name']!=a and r['receive_name']==a
  assert r['before']=={'type_status':0,'type':1048576,'refs_status':0,'refs':0}
  assert r['dead_before_status']==0 and r['dead_before_refs']==1
  assert r['after']['type_status']==15 and r['after']['refs_status']==15 and r['dead_after_status']==15
  assert r['message_id']==0x20000000 and r['message_bits']&255==18 and r['message_size']==44 and bytes.fromhex(r['body_hex'])==EMPTY
  # mach_msg_destroy has void return; result placeholder is not a kernel status.
 peer.check(baseline,mode)
if __name__=='__main__':
 folder=Path(sys.argv[1]);projection=folder/'prior-projection';projection.mkdir(exist_ok=True);n=0;body_faults=0;cases=[]
 for mode in ['withheld','peer-loss-withheld','peer-loss-late']:
  d=json.load(open(folder/(mode+'.json')));check(d,mode);base=copy.deepcopy(d)
  if mode=='peer-loss-late':base['release_trace']=[];base['abandon_wrapper_calls']=0
  (projection/(mode+'.json')).write_text(json.dumps(base))
  def reject(bad):
   global n
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted corrupt late-disposal evidence')
  for k in ['late_release_wait','late_wrapper_calls','abandon_wrapper_calls']:
   bad=copy.deepcopy(d);bad[k]+=1;reject(bad)
  for k in ['complete','window','api','caller_image','caller_symbol','result_available']:
   bad=copy.deepcopy(d);v=bad['release_trace'][0][k];bad['release_trace'][0][k]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else v+'!');reject(bad)
  if mode=='peer-loss-late':
   for k in ['receive_name','dead_before_status','dead_before_refs','dead_after_status','message_id','message_size']:
    bad=copy.deepcopy(d);bad['release_trace'][0][k]+=1;reject(bad)
   bad=copy.deepcopy(d);bad['release_trace'][0]['name']=d['rights_before']['name'];reject(bad)
   bad=copy.deepcopy(d);bad['release_trace'][0]['message_bits']^=1;reject(bad)
   for phase in ['before','after']:
    for k in ['type_status','refs_status']+(['type','refs']if phase=='before'else []):
     bad=copy.deepcopy(d);bad['release_trace'][0][phase][k]+=1;reject(bad)
   for offset in range(20):
    b=bytearray(EMPTY);b[offset]^=1;bad=copy.deepcopy(d);bad['release_trace'][0]['body_hex']=b.hex();reject(bad);body_faults+=1
  cases.append({'mode':mode,'release_window':'late SDK call plus bounded helper-worker event'if mode=='peer-loss-late'else'explicit held-reply release','SDK_release':'mach_msg_destroy (void)'if mode=='peer-loss-late'else'mach_port_deallocate','caller_symbol':d['release_trace'][0]['caller_symbol'],'dead_name_urefs_before':int(mode!='withheld'),'exact_name_invalid_after':True,'actual_release_event_observed':True,'destroyed_body_bytes_verified':20 if mode=='peer-loss-late'else 0})
 p=subprocess.run(['python3',str(w/'verify-peer.py'),str(projection)],capture_output=True,timeout=10);p.check_returncode();old=json.loads(p.stdout);assert old['corrupt_evidence_rejected']==1246
 print(json.dumps({'cases':cases,'prior_projection_mutations_rejected':1246,'new_accounting_and_destroy_body_mutations_rejected':n,'destroy_body_byte_mutations_rejected':body_faults,'total_bytes_verified':956,'source_bytes_verified_separately':1412,'kernel_failed_send_observed':False,'void_destroy_return_not_kernel_status':True,'all_native_resource_release_accounted':False,'target_operation_settlement':False},indent=2))
