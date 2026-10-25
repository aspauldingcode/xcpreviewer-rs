from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-reply-dispatch-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
def word(a):return struct.unpack_from('<I',data,a-base)[0]
def branch(a):
 i=word(a);assert i>>26 in [5,0x25];v=i&0x3ffffff;return a+4*(v-(1<<26) if v&(1<<25) else v)
def constant(a,b,reg):
 value=0
 for pc in range(base+a,base+b,4):
  i=word(pc);assert i&31==reg
  shift=((i>>21)&3)*16;v=((i>>5)&65535)<<shift
  if i&0x7f800000==0x52800000:value=v
  elif i&0x7f800000==0x72800000:value=(value&~(65535<<shift))|v
  else:raise AssertionError('unexpected constant opcode')
 return value

def rel(a):return a+struct.unpack_from('<i',data,a-base)[0]
def cstr(a):return c.read(a,128).split(b'\0')[0].decode()
def cb(a):
 i=word(base+a);assert i&0x7e000000==0x34000000;v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
# Follow the field descriptor and its symbolic type reference back to Kind.
fd=base+0xeab8;symbolic=rel(fd);assert c.read(symbolic,1)==b'\x01';kind=rel(symbolic+1)
assert kind==base+0xed70 and word(kind)&31==18 and cstr(rel(kind+8))=='Kind'
parent=rel(kind+4);assert word(parent)&31==17 and cstr(rel(parent+8))=='XPCError' and rel(kind+16)==fd
assert struct.unpack_from('<HHI',data,fd-base+8)==(3,12,5)
assert (word(kind+20)&0xffffff,word(kind+24))==(3,2)
fields=[]
for i in range(5):
 a=fd+16+12*i;name=cstr(rel(a+8));typ=rel(a+4) if word(a+4) else None
 fields.append({'name':name,'mangled_payload':cstr(typ) if typ else None})
assert fields==[{'name':n,'mangled_payload':('SS' if i<3 else None)} for i,n in enumerate(['connectionInvalidated','invalidType','unknown','connectionInterrupted','terminationImminent'])]

trie,uuid=c.exports(base);assert uuid=='fffb683f59433c2591b272d6e5174fa3'
# Match the actual enum producer, not guessed wire discriminants.
for a,v in [(0x8050,1),(0x808c,3),(0x80d8,0),(0x8110,3),(0x8190,2)]:assert constant(a,a+4,2)==v
assert constant(0x8084,0x8088,20)==0 and constant(0x8114,0x8118,20)==1
# Exact guards and optional closure slots; both paths precede unchanged error completion.
expected={0x5758:0x72001f48,0x575c:0x54000e00,0x5760:0x71000d1f,0x5764:0x54001021,0x5768:0xaa150308,0x576c:0xb5000fe8,0x5770:0xf9402293,0x5774:0xb4000fb3,0x5778:0xf9402694,0x5788:0xd73f0a71,0x591c:0xf9402a93,0x5920:0xb4000253,0x5924:0xf9402e94,0x5948:0xd73f0a71,0x5988:0xa9005438,0x598c:0x3900403a,0x5990:0xd2800000,0x5998:0xaa1703f4,0x59a0:0xd73f0ad1}
for off,value in expected.items():assert word(base+off)==value
# Decode conditional branch offsets with opcode checks.
def conditional(a):
 i=word(base+a);assert i&0xff000010==0x54000000 or i&0x7e000000==0x34000000
 v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
for a,b in [(0x575c,0x591c),(0x5764,0x5968),(0x576c,0x5968),(0x5774,0x5968),(0x5920,0x5968)]:assert conditional(a)==base+b
assert branch(base+0x578c)==base+0x595c
# Callback-context release then error-object creation; distinct request callback.
assert branch(base+0x5964)==base+0x71b8
assert branch(base+0x5a48)==base+0x5ddc
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x53e0,0x5ddc),(0x8004,0x81ac)];bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})

out={'services_text_sha256':sha(data),'image_uuid':uuid,'enum_fields':fields,'enum_descriptor':hex(kind),'notification_slots':{'interruption':64,'invalidation':80},'request_completion':'0x2633059a0','sequence':['classify XPC Kind','optional interruption or invalidation Void callback','forward nil and original Kind error to request callback'],'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'native_callback_invoked':False,'target_settlement_proven':False}
f=artifact/'findings.json'
assert out==json.loads(f.read_text())
print('Verified',out['selected_source_bytes_verified'],'source bytes');work.cleanup()
