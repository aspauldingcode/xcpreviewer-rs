from pathlib import Path
import json,struct,hashlib,sys,copy
u=lambda x:struct.pack('<I',x)
def pad(b):return b+b'\0'*((-len(b))%4)
def encode(v):
 if isinstance(v,bool):return u(0x2000)+u(v)
 if isinstance(v,int):return u(0x4000)+struct.pack('<Q',v)
 if isinstance(v,str):
  b=v.encode()+b'\0';return u(0x9000)+u(len(b))+pad(b)
 if isinstance(v,list):
  b=u(len(v))+b''.join(map(encode,v));return u(0xe000)+u(len(b))+b
 b=u(len(v))+b''.join(pad(k.encode()+b'\0')+encode(x)for k,x in v.items());return u(0xf000)+u(len(b))+b
def expected(holdout):
 action={'bsx_class':'BSAction'}
 if holdout:action['i']={'bsx_class':'BSSettings'}
 d={'bsxpc_CIDr':False,'bsxpc_CID':1,'1':{'bsx_class':'FBSSceneIdentity','i':'owned.scene.☃'if holdout else'owned.scene.primary'},'2':[action]}
 if not holdout:d['3']='owned.extension.primary'
 d['bsxpc_SEL']='sceneID:sendActions:toExtension:completion:'
 return b'CPX@'+u(5)+encode(d)
def check(d,mode):
 for k,v in {'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'independent_xpc_equal':1,'invocation_received':1,'action_completion_callbacks':1,'completion_error_matches':1}.items():assert d[k]==v,k
 matches=[x for x in d['trace']if b'sceneID:sendActions:'in bytes.fromhex(x['send_body_hex'])];assert len(matches)==1
 x=matches[0];assert x['api']==3 and x['complete']==1 and x['result']==0 and x['caller_image']=='/usr/lib/system/libdispatch.dylib'
 actual=bytes.fromhex(x['send_body_hex']);assert actual==expected(mode.endswith('holdout')),'entire XPC body including padding'
 return actual
if __name__=='__main__':
 root=Path(sys.argv[1]);out=[];mutations=0
 for mode in ['primary','holdout','error-primary','error-holdout','wrong-slot']:
  d=json.loads((root/(mode+'.json')).read_text());body=check(d,mode)
  for i in range(len(body)):
   m=copy.deepcopy(d);row=next(x for x in m['trace']if b'sceneID:sendActions:'in bytes.fromhex(x['send_body_hex']));b=bytearray(body);b[i]^=1;row['send_body_hex']=b.hex()
   try:check(m,mode)
   except AssertionError:mutations+=1
   else:raise AssertionError('accepted byte mutation')
  (root/(mode+'.body')).write_bytes(body)
  out.append({'mode':mode,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'all_bytes_equal':True,'mach2_calls':sum(x['api']==3 for x in d['trace'])})
 print(json.dumps({'cases':out,'body_byte_mutations_rejected':mutations,'mach_header_parity':False,'scene_execution':False,'settlement':False},indent=2))
