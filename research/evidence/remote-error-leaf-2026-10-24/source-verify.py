from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def reflect(a):
 fd=m.relative(a+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert kind==2 and size==12;return [m.string(m.relative(fd+16+i*size+8)) for i in range(n)]
keys=reflect(0x151d4c);assert keys==['errorTypeDescription','highValueTitle','lowValueTitle','additionalInfo','additionalDiagnostics','options','severity','isPotentialCrash','isNative']
assert reflect(0x151d14)==['leaf','wrapper'];assert reflect(0x151c0c)==['error','info']
sym,ind,libs=tables(m)
def import_at(a,width=12):
 sec=next(s for s in m.sections if s['flags']&255 in ({8} if width==12 else {6,7}) and s['address']<=a<s['address']+s['size']);i=index(m,sec,a,width,ind);n,k,ss,d,v=m.unpack('<IBBHQ',sym[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=sym[2]+n;return m.data[o:m.data.index(0,o)].decode()
imports={hex(a):import_at(a) for a in [0x12fc20,0x12fb84,0x131270]};assert imports=={'0x12fc20':'_$sSS9hasPrefixySbSSF','0x12fb84':'_$sSS6appendyySSF','0x131270':'_swift_dynamicCast'}
metadata={hex(a):import_at(a,8) for a in [0x171338,0x171228,0x170fe0]};assert metadata=={'0x171338':'_$sSiN','0x171228':'_$sSbN','0x170fe0':'_$sSSN'}
assert m.string(0x143aa0)=='[Remote] Unknown Error';assert m.string(0x143ac0)=='isPotentialCrash';assert m.string(0x143ae0)=='additionalDiagnostics';assert m.string(0x143b00)=='errorTypeDescription'
for a,t in [(0x60014,0x6041c),(0x600bc,0x6041c),(0x6012c,0x6041c),(0x60170,0x6041c),(0x601b0,0x6041c),(0x60268,0x619e0),(0x602ec,0x60558),(0x60320,0x606c0),(0x60350,0x606c0),(0x60060,0x12fc20),(0x60078,0x12fb84),(0x5f298,0x5ffcc),(0x61a38,0x131270),(0x60774,0x618ec),(0x5ff98,0xac550)]:assert call(a)==t
# Exact small string '[Remote] ' and missing Optional<Bool> tag2.
assert [word(a) for a in range(0x6003c,0x6004c,4)]==[0xd28a4b74,0xf2adacb4,0xf2ce8df4,0xf2ebacb4];assert word(0x60034)==0xd280041c and word(0x60038)==0xf2fd201c
assert word(0x607c0)==0x52800040
# Potential-crash ORs the None test before masking; native flag only masks.
assert [word(a) for a in range(0x603b0,0x603c0,4)]==[0x12001d09,0x7100093f,0x1a9f17e9,0x2a080137]
assert word(0x603c8)==0x120002e8 and word(0x603cc)==0x120002c9
matrix=[{'optional_bool_storage':v,'potential_crash':bool((v|int(v==2))&1),'native':bool(v&1)} for v in [0,1,2]];assert [x['potential_crash'] for x in matrix]==[False,True,True] and [x['native'] for x in matrix]==[False,True,False]
# Encoder stores the errorType='leaf' small strings and filters absent values.
assert word(0x5ff14)==0x528cad88 and word(0x5ff18)==0x72accc28
ranges=[]
for a,b in [(0x5fb98,0x6041c),(0x606c0,0x607e0),(0x619e0,0x61ad8),(0x5d578,0x5d624),(0x5f154,0x5f444),(0x6080c,0x60888)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'keys':keys,'error_types':['leaf','wrapper'],'severity':['error','info'],'imports':imports,'metadata_imports':metadata,'optional_bool_storage_source_matrix':matrix,'default_title':'[Remote] Unknown Error','prefix':'[Remote] ','canonical_profile_only':True,'wrapper_implemented':False,'native_private_runtime_invoked':False,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges)}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
