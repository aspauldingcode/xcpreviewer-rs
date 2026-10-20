"""Independent bounded Python decoder and owned native acceptance comparator."""
from pathlib import Path
import json,struct,base64,hashlib,sys,copy
sha=lambda b:hashlib.sha256(b).hexdigest()
def decode(b):
 assert len(b)<=64*1024*1024 and b[:8]==b'CPX@\x05\0\0\0';pos=8;nodes=0
 def take(n):
  nonlocal pos
  assert n>=0 and pos+n<=len(b);v=b[pos:pos+n];pos+=n;return v
 def word():return struct.unpack('<I',take(4))[0]
 def pad():assert not any(take((-pos)%4))
 def value(depth=0):
  nonlocal nodes
  nodes+=1;assert depth<=64 and nodes<=100000;t=word()
  if t==0x2000:
   n=word();assert n in [0,1];return {'type':'bool','value':bool(n)}
  if t in [0x3000,0x4000]:
   n=struct.unpack('<q' if t==0x3000 else '<Q',take(8))[0];return {'type':'int64' if t==0x3000 else 'uint64','value':n if t==0x3000 else str(n)}
  if t in [0x8000,0x9000]:
   d=take(word());pad()
   if t==0x8000:return {'type':'data','bytes':len(d),'base64':base64.b64encode(d).decode()}
   assert d[-1:]==b'\0' and b'\0' not in d[:-1];return {'type':'string','value':d[:-1].decode('utf8')}
  if t==0xb000:return {'type':'fd'}
  if t==0x1000:return {'type':'null'}
  if t==0x5000:return {'type':'double','bits':format(struct.unpack('<Q',take(8))[0],'016x')}
  assert t in [0xe000,0xf000];length=word();end=pos+length;assert end<=len(b);n=word();assert n<=100000;out=[] if t==0xe000 else {}
  for _ in range(n):
   if t==0xf000:
    z=b.index(0,pos);k=take(z-pos).decode('utf8');take(1);pad();assert k not in out;out[k]=value(depth+1)
   else:out.append(value(depth+1))
  assert pos==end;return {'type':'array' if t==0xe000 else 'dictionary','value':out}
 v=value();assert pos==len(b);return v

UUID='c40fcae87a173d8287cb3da4802adef1'
def compare(a,b,alias,size):
 assert len(a)==len(b)==size and struct.unpack_from('<I',a)[0]==struct.unpack_from('<I',b)[0]==2
 normalized=bytearray(a);sn=[];rn=[]
 for off in [4,16]:
  sn.append(int.from_bytes(a[off:off+4],'little'));rn.append(int.from_bytes(b[off:off+4],'little'));assert sn[-1] and rn[-1]
  assert a[off+4:off+10]==b[off+4:off+10]==bytes(6);assert a[off+10]==19 and b[off+10]==17 and a[off+11]==b[off+11]==0
  normalized[off:off+4]=b[off:off+4];normalized[off+10]=17
 assert (sn[0]==sn[1])==alias and (rn[0]==rn[1])==alias
 assert bytes(normalized)==b
 return a[28:]
def verify(folder):
 cases={};faults=0;total=0
 for mode in ['native','native-alias','native-holdout','portable','portable-alias','portable-holdout','wrong-order']:
  alias=mode.endswith('alias');good=mode!='wrong-order';d=folder/mode;p=json.loads((d/'parent.json').read_text())[0];c=json.loads((d/'child.json').read_text())[0]
  assert p['peer_role']==0 and c['peer_role']==1 and p['pid']!=c['pid']
  assert p['peer_setup_audit_verified'] and c['peer_setup_audit_verified'] and p['parent_reaped_child_before_receipt'] and p['reaped_before_fd_dup_and_read']
  assert p['scalar_bits_match'] and p['callbacks']==1 and p['callback_arrived'] and p['callback_on_owned_queue'] and p['callback_payload_matches']==good and p['received_descriptor_matches']==good
  assert p['received_descriptor_read_a']==23 and p['received_descriptor_read_b']==(0 if alias else 23)
  # Child's unused native reply right is explicitly retired by the redirect;
  # native send-once notification yields an error callback, not a payload reply.
  assert c['callbacks']==1 and not c['callback_payload_matches'] and c['received_descriptor_read_a']==-1
  send=next(x for x in c['trace']if x['send_id']==0x20000000 and x['result']==0);recv=next(x for x in p['trace']if x['receive_id']==0x20000000 and x['result']==0)
  assert send['caller_uuid']==recv['caller_uuid']==UUID and recv['receive_audit_pid']==c['pid']
  assert send['caller_offset']==214252 and recv['caller_offset']==213276
  assert sha(base64.b64decode(send['caller_prefix32']))=='6792e3a106dca3e24e5c3dac808f886f1f70120f49d29eaac4d3626d719628d1'
  assert sha(base64.b64decode(recv['caller_prefix32']))=='6f0941dfc37c76dd6cec5e93e2eb7ce4b1a866eca7adf6ab737790f80d1f8865'
  size=596 if mode.endswith('holdout')else 572
  assert send['send_bits']==0x80000012 and recv['receive_bits']==0x80001200 and send['send_size']==recv['receive_message_size']==size+24
  a=base64.b64decode(send['send_body']);b=base64.b64decode(recv['receive_body']);wire=compare(a,b,alias,size);tree=decode(wire)
  assert tree['value']['bsx_class']=={'type':'string','value':'BSActionResponse'}
  slots=tree['value']['bsx_auto']['value']['_info']['value']['objects']['value'];assert len(slots)==1 and slots[0]['value'][0]=={'type':'uint64','value':'1'}
  typed=slots[0]['value'][1];assert typed==c['typed_payload'];v=typed['value'];assert v['signed']=={'type':'int64','value':-9223372036854775808 if mode.endswith('holdout')else -7} and v['unsigned']=={'type':'uint64','value':'0'if mode.endswith('holdout')else '18446744073709551615'} and v['flag']=={'type':'bool','value':True} and v['bytes']=={'type':'data','base64':'AP8D','bytes':3} and v['text']=={'type':'string','value':'owned-snow☃'if mode.endswith('holdout')else 'owned-typed'}
  bits=[0xc004000000000000,0,0x000fffffffffffff,0x7fefffffffffffff,0xffefffffffffffff,0xfff8000000005678]if mode.endswith('holdout')else[0x3ff8000000000000,0x8000000000000000,1,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000001234]
  for name,n in zip(['finiteDouble','negativeZero','subnormal','positiveInfinity','negativeInfinity','quietNaN'],bits):assert v[name]=={'type':'double','bits':format(n,'016x')}
  assert v['nullValue']=={'type':'null'}
  for off in [0,4,8,13,14,15,16,20,26,27,28,len(b)//2,len(b)-1]:
   bad=bytearray(b)
   if off in [4,16]:bad[off:off+4]=bytes(4)
   else:bad[off]^=1
   try:compare(a,bad,alias,size)
   except AssertionError:faults+=1
   else:raise AssertionError('accepted mutated transfer')
  cases[mode]={'complex_body_bytes':len(a),'wire_bytes':len(wire),'sender_body_sha256':sha(a),'receiver_body_sha256':sha(b),'sender_audit_matches_owned_child':True,'native_callback_matches':good,'read_a':23,'read_b':0 if alias else 23,'wire_sha256':sha(wire)};total+=len(a)
 assert (folder/'native-order.txt').read_text().split()==['1','0'] and (folder/'native-alias-order.txt').read_text().split()==['1','0']
 assert cases['native']['wire_sha256']==cases['native-alias']['wire_sha256'] and cases['portable']['wire_sha256']==cases['portable-alias']['wire_sha256']==cases['wrong-order']['wire_sha256']
 assert cases['native']['wire_sha256']!=cases['portable']['wire_sha256']
 return {'cases':cases,'complex_body_bytes_compared':total,'faults_rejected':faults,'wrong_order_semantic_failure_detected':True,'native_xpc_cross_process':True,'native_canvas_transport':False,'final_right_retirement_proven':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
