"""Compare every owned complex-message byte with SDK-defined rewrites."""
from pathlib import Path
import json,struct,base64,hashlib,sys
sha=lambda b:hashlib.sha256(b).hexdigest()
def receipt(path,alias,expected=True):
 v=json.loads(path.read_text())[0];assert v['callback_arrived'] and v['callbacks']==1 and v['callback_on_owned_queue'];assert bool(v['received_descriptor_matches'])==expected and bool(v['callback_payload_matches'])==expected
 assert v['original_pipe_closed_before_encoding'];assert v['source_descriptor_calls']==(1 if alias else 2);assert bool(v['source_descriptor_number_reused'])==(not alias)
 assert v['received_descriptor_read_a']==23 and v['received_descriptor_read_b']==(0 if alias else 23)
 send=next(t for t in v['trace'] if t['send_id']==536870912 and t['result']==0);recv=next(t for t in v['trace'] if t['receive_id']==536870912 and t['result']==0);assert send['send_bits']==0x80000012 and recv['receive_bits']==0x80001200
 assert send['caller_uuid']==recv['caller_uuid']=='c40fcae87a173d8287cb3da4802adef1';a=base64.b64decode(send['send_body']);b=base64.b64decode(recv['receive_body']);assert len(a)==len(b) and send['send_size']==recv['receive_message_size']==len(a)+24 and struct.unpack_from('<I',a)[0]==struct.unpack_from('<I',b)[0]==2
 names=[];normalized=bytearray(a)
 for i in range(2):
  o=4+i*12;name=struct.unpack_from('<I',a,o)[0];assert name!=0 and a[o+4:o+10]==b'\0'*6 and a[o+10]==19 and a[o+11]==0;assert b[o+10]==17;normalized[o+10]=17;names.append(name)
 assert bytes(normalized)==b;assert (names[0]==names[1])==alias
 wire=a[28:];assert wire[:8]==b'CPX@\x05\0\0\0';return {'entire_complex_body_bytes':len(a),'wire_bytes':len(wire),'body_sha256':sha(a),'wire_sha256':sha(wire),'descriptor_count':2,'source_same_fd_number_reused':not alias,'same_kernel_port_name_in_alias_case':alias,'expected_read_a':23,'expected_read_b':0 if alias else 23,'payload_matched':expected,'kernel_disposition_rewrite_offsets':[14,26]},wire

def verify(folder):
 result={};total=0
 for mode,alias in [('native',False),('native-alias',True)]:
  a,original=receipt(folder/(mode+'.stdout'),alias);p,portable=receipt(folder/(mode+'-portable.stdout'),alias);assert original!=portable
  order=[int(x)for x in (folder/(mode+'-order.txt')).read_text().split()];assert order==[1,0];assert portable==(folder/(mode+'-portable.bin')).read_bytes();assert original==(folder/(mode+'-wire.bin')).read_bytes();result[mode]={'native':a,'portable':p,'descriptor_order':order};total+=a['entire_complex_body_bytes']+p['entire_complex_body_bytes']
 wrong,_=receipt(folder/'native-wrong-order-portable.stdout',False,False);assert not wrong['payload_matched']
 # Falsify the byte comparator without invoking native private decoders.
 native=json.loads((folder/'native.stdout').read_text())[0];send=next(t for t in native['trace']if t['send_id']==536870912);recv=next(t for t in native['trace']if t['receive_id']==536870912);a=base64.b64decode(send['send_body']);b=base64.b64decode(recv['receive_body']);correct=bytearray(a);correct[14]=correct[26]=17;assert bytes(correct)==b
 for offset in [0,4,8,14,26,28,len(b)//2,len(b)-1]:
  bad=bytearray(b);bad[offset]^=1;assert bytes(correct)!=bytes(bad)
 return {'cases':result,'total_complex_body_bytes_compared':total,'intentional_wrong_order_semantic_failure_detected':True,'byte_faults_rejected':8,'portable_projection_only':True,'os_capability_execution_implemented':False,'cross_process_canvas':False,'final_right_retirement_proven':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]))))
