"""Pinned offline reply-source verification. Does not execute native functions."""
from pathlib import Path
import sys,json,hashlib,subprocess,re,plistlib
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost')
sha=lambda b:hashlib.sha256(b).hexdigest();pin='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';assert sha(m.data)==pin
s,ind,libs=tables(m);sec=next(t for t in m.sections if t['flags']&255==8)
def binding(a):
 i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return {'symbol':m.data[o:m.data.index(0,o)].decode(),'library':libs[(d>>8)-1]}
bindings={hex(a):binding(a) for a in [0xb22c0,0xb1558,0xb1930,0xb1834,0xb1cf0,0xb22fc]}
for a,part in [(0xb22c0,'_stdlib_isOSVersionAtLeast'),(0xb1558,'DataV36_unconditionallyBridgeFromObjectiveC'),(0xb1930,'PropertyListV22serializableDictionary'),(0xb1834,'ContinuationV6resume'),(0xb1cf0,'PromiseC7fulfill'),(0xb22fc,'humanReadable')]:assert part in bindings[hex(a)]['symbol']
def word(a):return m.u32(m.file_offset(a))
def branch(a):
 i=word(a);assert i>>26 in [5,0x25];n=i&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def cbz(a,register,target):
 i=word(a);assert i&0xff00001f==0xb4000000|register;n=(i>>5)&0x7ffff;assert a+4*(n-(1<<19) if n&(1<<18) else n)==target
cbz(0x3fce0,0,0x3fd88);cbz(0x3fd8c,1,0x3ffa0)
for a,t in [(0x3fd34,0xb22c0),(0x3fd4c,0xb28e0),(0x3fee8,0xb2960),(0x3fd5c,0xb1558),(0x3ff2c,0xb1930),(0x3fe58,0xb22fc),(0x3ff78,0xb1834),(0x40038,0xb1834),(0x400a0,0xb1834),(0x3fb30,0xb1cf0),(0x6ea60,0xb2a00),(0x6eae4,0xb1930),(0x6eb3c,0x470c0)]:
 assert branch(a)==t
assert branch(0x3ffe8)==0x41220
# Source-specific OS gate, serialized/deserialized tags and success/failure tags.
for a,v in {0x3fd28:0x528001c0,0x3fd2c:0x52800081,0x3fd30:0xd2800002,0x3fd80:0x52800022,0x3ff3c:0x52800002,0x3ff50:0x52800002,0x40010:0x52800022,0x40088:0x52800022,0x6ea1c:0x7100041f}.items():assert word(a)==v
fd=m.relative(0xd1648+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert kind==2 and size==12 and n==2;cases=[m.string(m.relative(fd+16+i*size+8)) for i in range(n)];assert cases==['deserialized','serialized']
# This exact five-instruction counter body returns old value and wraps ADD.
assert [word(a) for a in range(0x60a10,0x60a24,4)]==[0xf9400009,0x9100052a,0xf900000a,0xf9000109,0xd65f03c0]
fixtures=r/'tools/re/rust/canvas-core/tests/fixtures/transport-reply';expected={'padding':bytes(range(128)),'reply':{'message':'owned/🪨','sequence':-17}}
for name,value in [('dictionary',expected),('array',[1,'not dictionary'])]:assert (fixtures/(name+'.bplist')).read_bytes()==plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=True)
bodies=[]
for a,b in [(0x3fcb8,0x40114),(0x3fb1c,0x3fb40),(0x6e998,0x6ebb8),(0x60a10,0x60a24)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));bodies.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
print(json.dumps({'image_sha256':pin,'uuid':m.uuid,'import_bindings':bindings,'lazy_cases':cases,'payload_precedes_error':True,'empty_reply_on_both_absent':True,'uvpropertylist_data_gate':[14,4,0],'serialized_data_parsed_in_getter':True,'dictionary_required_after_native_deserialization':True,'counter_step_returns_old_and_wraps':True,'identifier_initial_value_and_format_recovered':False,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'source_only':True,'native_functions_invoked':False,'native_nserror_projection_reproduced':False,'target_settlement_proven':False},indent=2))
