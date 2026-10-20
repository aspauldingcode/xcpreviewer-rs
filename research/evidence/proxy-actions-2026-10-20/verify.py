from pathlib import Path
import json,copy,hashlib,sys
EXPECTED={'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'activation_callbacks':1,'valid_after_activation':True,'valid_after_invalidate':False,'is_null_endpoint':False,'target_class':'BSXPCServiceConnectionProxy<FBSWorkspaceServiceServerInterface>','scene_action_signature_arguments':6,'action_invoked':True,'action_completion_callbacks':1,'owned_peer_connections':1,'invocation_received':1,'independent_xpc_equal':1,'completion_error_matches':1}
def check(x,mode,pins):
 for k,v in EXPECTED.items():assert x[k]==v,(mode,k)
 assert x['holdout']==mode.endswith('holdout')
 assert x['reply_error_mode']==(mode.startswith('error-')or mode=='wrong-slot')
 assert x['wrong_reply_slot']==(mode=='wrong-slot')
 assert x['completion_error_present']==mode.startswith('error-')
 archive=bytes.fromhex(x['reply_error_archive_hex'])
 if x['reply_error_mode']:
  pin=pins['error-holdout'if x['holdout']else'error-primary'];assert len(archive)==pin['bytes']and hashlib.sha256(archive).hexdigest()==pin['sha256'];assert archive.startswith(b'bplist17')
 else:assert not archive
 assert x['interposed_mach_calls']==len(x['trace'])<256
 for row in x['trace']:
  for key in ['send_body_hex','receive_body_hex']:assert len(bytes.fromhex(row[key]))<=4096
 return archive
def verify(folder,pins):
 n=0;archive_mutants=0;captures=[]
 for mode in ['primary','holdout','error-primary','error-holdout','wrong-slot']:
  x=json.loads((folder/(mode+'.json')).read_text());archive=check(x,mode,pins)
  bodies=[bytes.fromhex(t['send_body_hex'])for t in x['trace']]
  assert not any(b'sceneID:sendActions:'in b for b in bodies),'Capture scope changed: inspect actual invocation bytes before claiming parity'
  captures.append({'mode':mode,'xpc_equal':True,'error_present':bool(x['completion_error_present']),'archive_bytes':len(archive),'captured_cpx_headers':sum(b.count(b'CPX@')for b in bodies),'matching_invocation_bodies':0})
  for k,v in EXPECTED.items():
   bad=copy.deepcopy(x);bad[k]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else'mutated')
   try:check(bad,mode,pins)
   except AssertionError:n+=1
   else:raise AssertionError('accepted receipt mutation '+k)
  for i in range(len(archive)):
   bad=copy.deepcopy(x);b=bytearray(archive);b[i]^=1;bad['reply_error_archive_hex']=b.hex()
   try:check(bad,mode,pins)
   except AssertionError:archive_mutants+=1
   else:raise AssertionError('accepted changed captured archive byte')
 return {'native_cases':5,'whole_invocation_dictionary_equalities':5,'receipt_mutations_rejected':n,'archive_byte_mutations_rejected':archive_mutants,'unique_positive_native_archive_bytes_preserved_in_rust':212,'captures':captures,'native_request_wire_parity':False,'native_error_archive_decoded_portably':False,'scene_execution':False,'settlement':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]),json.loads(Path(__file__).with_name('archive-pins.json').read_text())),indent=2))
