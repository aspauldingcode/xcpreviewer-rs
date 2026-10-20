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
  assert t in [0xe000,0xf000];length=word();end=pos+length;assert end<=len(b);n=word();assert n<=100000;out=[] if t==0xe000 else {}
  for _ in range(n):
   if t==0xf000:
    z=b.index(0,pos);k=take(z-pos).decode('utf8');take(1);pad();assert k not in out;out[k]=value(depth+1)
   else:out.append(value(depth+1))
  assert pos==end;return {'type':'array' if t==0xe000 else 'dictionary','value':out}
 v=value();assert pos==len(b);return v
def verify(folder):
 cases={};total=0
 for name,mode in [('body','native'),('holdout-body','native-holdout')]:
  native=json.loads((folder/(mode+'.stdout')).read_text())[0];portable=json.loads((folder/(name+'-portable.stdout')).read_text())[0]
  original=(folder/(name+'.bin')).read_bytes();candidate=(folder/(name+'-portable.bin')).read_bytes();a=decode(original);b=decode(candidate);assert a==b and original!=candidate
  assert a['value']['bsx_class']=={'type':'string','value':'BSActionResponse'}
  info=a['value']['bsx_auto']['value']['_info']['value'];assert info['bsx_class']=={'type':'string','value':'BSSettings'};slots=info['objects']['value'];assert len(slots)==1;parts=slots[0]['value'];assert len(parts)==2 and parts[0]=={'type':'uint64','value':'1'};assert parts[1]==native['typed_payload']
  for receipt,bytes_ in [(native,original),(portable,candidate)]:
   assert receipt['callbacks']==1 and receipt['callback_payload_matches'] and receipt['callback_on_owned_queue'] and receipt['callback_arrived'];send=next(t for t in receipt['trace'] if t['send_id']==536870912 and t['result']==0);recv=next(t for t in receipt['trace'] if t['receive_id']==536870912 and t['result']==0)
   assert send['caller_uuid']==recv['caller_uuid']=='c40fcae87a173d8287cb3da4802adef1';assert base64.b64decode(send['send_body'])==base64.b64decode(recv['receive_body'])==bytes_;assert send['send_size']==recv['receive_message_size']==len(bytes_)+24;total+=len(bytes_)
  rejected=0
  for mutate in range(8):
   x=bytearray(candidate)
   if mutate<4:x[[0,4,8,len(x)-1][mutate]]^=0x40
   elif mutate==4:x=x[:-1]
   elif mutate==5:x.extend(b'\0')
   elif mutate==6:x[12:16]=b'\xff'*4
   else:x[16:20]=b'\xff'*4
   try:decode(bytes(x))
   except (AssertionError,ValueError,UnicodeDecodeError,struct.error,IndexError):rejected+=1
  assert rejected==8;cases[name]={'native_bytes':len(original),'portable_bytes':len(candidate),'native_sha256':sha(original),'portable_sha256':sha(candidate),'semantic_tree_equal':True,'native_accepts_portable_order':True,'body_mutants_rejected':rejected}
 assert total==1360
 return {'cases':cases,'total_native_portable_body_bytes_compared':total,'native_acceptance_cases':2,'wire_version':5,'supported_observed_tags':[8192,12288,16384,32768,36864,57344,61440],'attachments_supported':False,'live_canvas_transport':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]))))
