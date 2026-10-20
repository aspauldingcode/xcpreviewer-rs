from pathlib import Path
import json,hashlib,struct,copy,sys
u=lambda n:struct.pack('<I',n)
def pad(b):return b+b'\0'*((-len(b))%4)
def enc(x):
 if isinstance(x,bytes):return u(0x8000)+u(len(x))+pad(x)
 if isinstance(x,str):
  b=x.encode()+b'\0';return u(0x9000)+u(len(b))+pad(b)
 b=u(len(x))+b''.join(pad(k.encode()+b'\0')+enc(v)for k,v in x.items());return u(0xf000)+u(len(b))+b
def check(d,mode,pins):
 holdout=mode.endswith('holdout');key='1'if mode=='argument-primary'else('BSXPCReturnValue'if mode=='reserved-value-primary'else'BSXPCReturnError');conflict=mode.startswith('conflict-');both=conflict or mode=='combined-error-primary';has_error=mode!='reserved-value-primary'
 expected={'boardservices_uuid_verified':True,'baseboard_uuid_verified':True,'independent_xpc_equal':1,'invocation_received':1,'action_completion_callbacks':1,'completion_error_present':int(has_error),'service_reply_key':key,'include_numbered':both,'holdout':holdout,'observed_error_domain':('Owned.Reply.☃'if holdout else'Owned.Reply')if has_error else'','observed_error_code':(29 if holdout else 17)if has_error else 0}
 for k,v in expected.items():assert d[k]==v,(mode,k)
 def archive(k,pin):
  b=bytes.fromhex(d[k]);assert len(b)==pin['bytes']and hashlib.sha256(b).hexdigest()==pin['sha256'];return b
 a=archive('reply_error_archive_hex',pins['error-holdout'if holdout else'error-primary']);alt=archive('alternate_archive_hex',pins['alternate'])if conflict else b''
 if not conflict:assert not d['alternate_archive_hex']
 def error(b):return {'bsx_class':'NSError','root':b}
 value={'1':error(alt if conflict else a),key:error(a)} if both else {key:error(a)}
 indices=[i for i,r in enumerate(d['trace'])if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex'])];assert len(indices)==1
 rows=[r for r in d['trace'][indices[0]+1:]if r['api']==3 and r['send_id']==0x20000000 and bytes.fromhex(r['send_body_hex']).startswith(b'CPX@')];assert len(rows)==1
 row=rows[0];assert row['complete']==1 and row['result']==0;body=bytes.fromhex(row['send_body_hex']);assert body==b'CPX@'+u(5)+enc(value),'complete reply-body byte/padding equality'
 return body,a
if __name__=='__main__':
 folder=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=False);pins=json.load(open(Path(__file__).with_name('service-archive-pins.json')));cases=[];mutants=0;receipt_mutants=0
 for mode in ['argument-primary','reserved-error-primary','reserved-error-holdout','reserved-value-primary','combined-error-primary','conflict-primary','conflict-holdout']:
  d=json.load(open(folder/(mode+'.json')));body,a=check(d,mode,pins);(out/(mode+'.body')).write_bytes(body);(out/(mode+'.archive')).write_bytes(a)
  request=next(i for i,r in enumerate(d['trace'])if b'sceneID:sendActions:'in bytes.fromhex(r['send_body_hex']));index=next(i for i,r in enumerate(d['trace'])if i>request and r['api']==3 and r['send_id']==0x20000000 and bytes.fromhex(r['send_body_hex']).startswith(b'CPX@'))
  for i in range(len(body)):
   bad=copy.deepcopy(d);b=bytearray(body);b[i]^=1;bad['trace'][index]['send_body_hex']=b.hex()
   try:check(bad,mode,pins)
   except AssertionError:mutants+=1
   else:raise AssertionError('accepted changed reply byte')
  for k in ['action_completion_callbacks','completion_error_present','observed_error_domain','observed_error_code']:
   bad=copy.deepcopy(d);v=bad[k];bad[k]=v+1 if isinstance(v,int)else v+'!'
   try:check(bad,mode,pins)
   except AssertionError:receipt_mutants+=1
   else:raise AssertionError('accepted changed callback evidence')
  cases.append({'mode':mode,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'reserved_error_precedes_numbered':mode.startswith('conflict-'),'native_error_present':mode!='reserved-value-primary'})
 print(json.dumps({'cases':cases,'reply_byte_mutations_rejected':mutants,'callback_receipt_mutations_rejected':receipt_mutants,'scene_execution':False,'target_operation_settlement':False},indent=2))
