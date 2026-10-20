from pathlib import Path
import hashlib,json,struct,copy,sys,importlib.util
u=lambda x:struct.pack('<I',x)
def pad(b):return b+b'\0'*((-len(b))%4)
def encode(v):
 if isinstance(v,bytes):return u(0x8000)+u(len(v))+pad(v)
 if isinstance(v,str):
  b=v.encode()+b'\0';return u(0x9000)+u(len(b))+pad(b)
 b=u(len(v))+b''.join(pad(k.encode()+b'\0')+encode(x)for k,x in v.items());return u(0xf000)+u(len(b))+b
def check(x,mode,pins):
 for k,v in {'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'independent_xpc_equal':1,'invocation_received':1,'action_completion_callbacks':1,'completion_error_matches':1}.items():assert x[k]==v,k
 assert x['completion_error_present']==mode.startswith('error-')
 archive=bytes.fromhex(x['reply_error_archive_hex'])
 if mode.startswith('error-')or mode=='wrong-slot':
  pin=pins['error-holdout'if mode.endswith('holdout')else'error-primary'];assert len(archive)==pin['bytes']and hashlib.sha256(archive).hexdigest()==pin['sha256']
  expected={'2'if mode=='wrong-slot'else'1':{'bsx_class':'NSError','root':archive}}
 else:assert not archive;expected={}
 request_indices=[i for i,r in enumerate(x['trace'])if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex'])];assert len(request_indices)==1
 matches=[r for r in x['trace'][request_indices[0]+1:]if r['api']==3 and r['send_id']==0x20000000 and bytes.fromhex(r['send_body_hex']).startswith(b'CPX@')];assert len(matches)==1
 row=matches[0];assert row['result']==0and row['complete']==1and row['caller_image']=='/usr/lib/system/libdispatch.dylib';actual=bytes.fromhex(row['send_body_hex']);assert actual==b'CPX@'+u(5)+encode(expected),'full reply body equality';return actual,expected
if __name__=='__main__':
 folder=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=False);pins=json.load(open(Path(__file__).with_name('archive-pins.json')));cases=[];n=0
 for mode in ['primary','holdout','error-primary','error-holdout','wrong-slot']:
  x=json.load(open(folder/(mode+'.json')));b,expected=check(x,mode,pins);(out/(mode+'.body')).write_bytes(b)
  if x['reply_error_archive_hex']:(out/(mode+'.archive')).write_bytes(bytes.fromhex(x['reply_error_archive_hex']))
  for i in range(len(b)):
   bad=copy.deepcopy(x);request_index=next(i for i,r in enumerate(bad['trace'])if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex']));r=next(r for r in bad['trace'][request_index+1:]if r['api']==3 and r['send_id']==0x20000000 and bytes.fromhex(r['send_body_hex']).startswith(b'CPX@'));v=bytearray(b);v[i]^=1;r['send_body_hex']=v.hex()
   try:check(bad,mode,pins)
   except AssertionError:n+=1
   else:raise AssertionError('accepted changed body byte')
  cases.append({'mode':mode,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'native_completion_error_present':bool(x['completion_error_present']),'all_reply_body_bytes_equal':True})
 print(json.dumps({'cases':cases,'reply_byte_mutants_rejected':n,'archive_semantic_encoding_portable':False,'mach_header_parity':False,'target_operation_settlement':False},indent=2))
