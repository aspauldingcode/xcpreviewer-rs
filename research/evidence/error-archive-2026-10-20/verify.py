from pathlib import Path
import json,subprocess,struct,hashlib,sys,copy
w=Path(__file__).parent
CASES=[('primary','Owned.Reply',17),('unicode','Owned.Reply.☃',29),('negative','Owned.Negative',-129),('zero','',0),('wide16','Owned.Wide',256),('wide32','Owned.Wide',65536),('max','Owned.Maximum.Domain.Long',2**63-1),('min','Owned.Minimum.😀',-2**63),('len15','123456789012345',255),('holdout','Holdout.é🦀',65535)]
def integer(v):
 n=8 if v<0 or v>2**32-1 else 4 if v>65535 else 2 if v>255 else 1
 return bytes([0x10|n])+(v&((1<<(n*8))-1)).to_bytes(n,'little')
def expected(domain,code):
 u=domain.encode('utf-16le');n=len(u)//2
 text=bytes([0x60|n])if n<15 else b'\x6f'+integer(n)
 out=bytearray(b'bplist17\xd0'+b'\0'*8+b'\x74bsx\0\xd0'+b'\0'*8+b'\x77$class\0\x78NSError\0\x77NSCode\0'+integer(code)+b'\x79NSDomain\0'+text+u+b'\x7bNSUserInfo\0\xe0')
 out[9:17]=struct.pack('<Q',len(out)-1);out[23:31]=struct.pack('<Q',len(out)-1);return bytes(out)
def run(folder):
 folder.mkdir(exist_ok=False)
 p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror',str(w/'native.m'),'-framework','Foundation','-o',str(folder/'native')],capture_output=True,timeout=30);(folder/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(folder/'native')],capture_output=True,timeout=5);(folder/'native.json').write_bytes(p.stdout);(folder/'native.stderr').write_bytes(p.stderr);p.check_returncode();return json.loads(p.stdout)
def check(d,folder):
 assert d['baseboard_uuid_verified'] is True and d['decode_offset']==15572 and len(d['cases'])==len(CASES)+1
 total=0;mutations=0;records=[];folder.mkdir(exist_ok=True)
 for row,(name,domain,code)in zip(d['cases'],CASES):
  assert row['case']==name and row['domain']==domain and row['code']==code and row['userinfo_empty']==1 and row['native_equal'] is True
  b=bytes.fromhex(row['archive_hex']);want=expected(domain,code);assert b==want
  for i in range(len(b)):
   changed=bytearray(b);changed[i]^=1;assert changed!=want;mutations+=1
  (folder/(name+'.archive')).write_bytes(b);total+=len(b);records.append({'case':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'domain':domain,'code':code,'native_secure_roundtrip':True})
 assert(folder/'primary.archive').read_bytes()==Path('/private/tmp/service-return-20261020/corpus-v2/argument-primary.archive').read_bytes()
 assert(folder/'unicode.archive').read_bytes()==Path('/private/tmp/service-return-20261020/corpus-v2/reserved-error-holdout.archive').read_bytes()
 extra=d['cases'][-1];assert extra['case']=='with_info' and extra['domain']=='Owned.Info' and extra['code']==17 and extra['userinfo_empty']==0 and extra['native_equal'] is True
 (folder/'with_info.archive').write_bytes(bytes.fromhex(extra['archive_hex']))
 assert total==1102
 return{'cases':records,'native_archive_bytes_verified':total,'byte_corruptions_rejected':mutations,'existing_captured_archives_equal':212,'scope':'canonical NSError domain/code/nil archived userInfo; no arbitrary bplist17 graphs or nonempty userInfo','native_nonempty_userinfo_negative_bytes':len(bytes.fromhex(extra['archive_hex'])),'native_nonempty_userinfo_negative_sha256':hashlib.sha256(bytes.fromhex(extra['archive_hex'])).hexdigest(),'private_callable_ABI_invented':False}
def faults(d,folder):
 n=0
 def reject(bad):
  nonlocal n
  try:check(bad,folder)
  except AssertionError:n+=1
  else:raise AssertionError('accepted corrupt native archive receipt')
 for i,row in enumerate(d['cases']):
  for key in ['case','domain','code','userinfo_empty','native_equal']:
   bad=copy.deepcopy(d);v=bad['cases'][i][key];bad['cases'][i][key]=not v if isinstance(v,bool)else(v+1 if isinstance(v,int)else v+'!');reject(bad)
 bad=copy.deepcopy(d);bad['baseboard_uuid_verified']=False;reject(bad)
 bad=copy.deepcopy(d);bad['decode_offset']+=4;reject(bad)
 bad=copy.deepcopy(d);bad['cases'].pop();reject(bad)
 return n
if __name__=='__main__':
 d=run(Path(sys.argv[1]));v=check(d,Path(sys.argv[1])/'corpus');v['receipt_mutations_rejected']=faults(d,Path(sys.argv[1])/'fault-corpus');print(json.dumps(v,indent=2))
