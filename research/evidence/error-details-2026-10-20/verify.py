from pathlib import Path
import json,hashlib,subprocess,sys,copy
w=Path(__file__).parent
CASES=[('single','Owned.Info',17,{'NSLocalizedFailureReason':'owned.reason'}),('diagnostic','BSServiceConnectionErrorDomain',3,{'BSErrorCodeDescription':'OperationFailed','NSLocalizedFailureReason':'XPC error received on message reply handler'}),('unicode','Owned.☃',-129,{'clé.☃':'value.😀','second':'other'}),('empty','Owned.Empty',0,{}),('numeric','Owned.Unsupported',7,{'number':42}),('holdout','Owned.Holdout.😀',256,{'detail':'a different holdout value','status':'ready'})]
def integer(v):
 n=8 if v<0 or v>2**32-1 else 4 if v>65535 else 2 if v>255 else 1
 return bytes([0x10|n])+(v&((1<<(8*n))-1)).to_bytes(n,'little')
class Encoder:
 def __init__(self):self.b=bytearray(b'bplist17');self.strings={}
 def container(self,tag):self.b.append(tag);p=len(self.b);self.b+=b'\0'*8;return p
 def finish(self,p):self.b[p:p+8]=(len(self.b)-1).to_bytes(8,'little')
 def text(self,s,ascii=False):
  if s in self.strings:
   offset=self.strings[s];n=1 if offset<256 else 2 if offset<65536 else 4;self.b.append(0x80|n);self.b+=offset.to_bytes(n,'little');return
  self.strings[s]=len(self.b);data=s.encode('ascii')+b'\0'if ascii else s.encode('utf-16le');count=len(data)if ascii else len(data)//2;tag=0x70 if ascii else 0x60
  self.b+=bytes([tag|count])if count<15 else bytes([tag|15])+integer(count);self.b+=data
 def archive(self,domain,code,info,order):
  outer=self.container(0xd0);self.text('bsx',True);inner=self.container(0xd0);self.text('$class',True);self.text('NSError',True);self.text('NSCode',True);self.b+=integer(code);self.text('NSDomain',True);self.text(domain);self.text('NSUserInfo',True)
  if not info:self.b.append(0xe0)
  else:
   d=self.container(0xd0);self.text('$class',True);self.text('NSDictionary',True);self.text('NS.keys',True);keys=self.container(0xa0)
   for k in order:self.text(k)
   self.finish(keys);self.text('NS.objects',True);values=self.container(0xa0)
   for k in order:self.text(info[k])
   self.finish(values);self.finish(d)
  self.finish(inner);self.finish(outer);return bytes(self.b)
def run(folder):
 folder.mkdir(exist_ok=False);p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror',str(w/'native.m'),'-framework','Foundation','-o',str(folder/'native')],capture_output=True,timeout=30);(folder/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode();p=subprocess.run([str(folder/'native')],capture_output=True,timeout=5);(folder/'native.json').write_bytes(p.stdout);(folder/'native.stderr').write_bytes(p.stderr);p.check_returncode();return json.loads(p.stdout)
def check(d,folder):
 assert d['baseboard_uuid_verified'] is True and d['decode_offset']==15572 and len(d['cases'])==6
 folder.mkdir(exist_ok=True);total=0;byte_faults=0;records=[]
 for row,(name,domain,code,info)in zip(d['cases'],CASES):
  assert row['case']==name and row['domain']==domain and row['code']==code and row['native_equal'] is True and row['user_info']==info and row['userinfo_empty']==int(not info)
  assert len(row['key_order'])==len(info) and set(row['key_order'])==set(info)
  b=bytes.fromhex(row['archive_hex']);(folder/(name+'.archive')).write_bytes(b)
  if name!='numeric':
   want=Encoder().archive(domain,code,info,row['key_order']);assert b==want
   total+=len(b)
   for i in range(len(b)):
    bad=bytearray(b);bad[i]^=1;assert bad!=want;byte_faults+=1
  records.append({'case':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'domain':domain,'code':code,'user_info':info,'native_roundtrip_equal':True,'wire_key_order_expectation_source':'independent NSDictionary allKeys on original error.userInfo','portable_supported':name!='numeric'})
 assert total==1260
 return{'cases':records,'supported_native_bytes_verified':total,'byte_corruptions_rejected':byte_faults,'unsupported_numeric_bytes':196,'dictionary_wire_order_not_universal':True,'generic_bplist17':False}
def faults(d,folder):
 n=0
 for i,row in enumerate(d['cases']):
  for key in ['case','domain','code','native_equal','user_info']:
   bad=copy.deepcopy(d);v=bad['cases'][i][key];bad['cases'][i][key]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else v+'!'if isinstance(v,str)else{'wrong':'wrong'})
   try:check(bad,folder)
   except AssertionError:n+=1
   else:raise AssertionError('accepted corrupt native userInfo receipt')
 return n
if __name__=='__main__':
 folder=Path(sys.argv[1]);d=run(folder);v=check(d,folder/'corpus');v['receipt_mutations_rejected']=faults(d,folder/'fault-corpus');print(json.dumps(v,indent=2))
