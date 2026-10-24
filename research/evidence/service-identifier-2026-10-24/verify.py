"""Source-only private framework checks plus an owned public Swift format control."""
from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');pin='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)==pin
s,ind,libs=tables(m)
def binding(a):
 sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);stride=12 if sec['flags']&255==8 else 8;assert sec['flags']&255 in [6,7,8]
 i=index(m,sec,a,stride,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return {'symbol':m.data[o:m.data.index(0,o)].decode(),'library':libs[(d>>8)-1]}
imports=[0xb1d14,0xb2284,0xb1c6c,0xb277c,0xe47e0,0xe47e8,0xb15b8,0xb15c4];bindings={hex(a):binding(a) for a in imports}
for a,part in [(0xb1d14,'OSAllocatedUnfairLockV22PreviewsFoundationHostE5value'),(0xb2284,'CustomStringConvertibleP11description'),(0xb1c6c,'SynchronousAccessProvidingPAAE9syncWrite'),(0xb277c,'swift_once'),(0xe47e0,'UInt64VN'),(0xe47e8,'UInt64Vs23CustomStringConvertiblesWP'),(0xb15b8,'ServiceConnectionC4send7message12replyHandler'),(0xb15c4,'ServiceConnectionC4send7messagey')]:assert part in bindings[hex(a)]['symbol']
def word(a):return m.u32(m.file_offset(a))
def branch(a):
 i=word(a);assert i>>26 in [5,0x25];v=i&0x3ffffff;return a+4*(v-(1<<26) if v&(1<<25) else v)
for a,t in [(0x609f8,0xb1d14),(0x60684,0xb1c6c),(0x606b0,0xb2284),(0x60708,0xb277c),(0x74910,0xb15c4),(0x74a0c,0xb15b8),(0x74904,0x49548),(0x74940,0x49548),(0x74c54,0x74790)]:assert branch(a)==t
def adrp_add(a):
 i=word(a);j=word(a+4);assert i&0x9f000000==0x90000000 and j&0xffc00000==0x91000000;d=i&31;assert j&31==d and (j>>5)&31==d;return pc_relative(i,a,True)+((j>>10)&4095)
assert adrp_add(0x60654)==0x60a10;assert adrp_add(0x60700)==0x609dc;assert adrp_add(0x60664)==0xf8720;assert adrp_add(0x749f8)==0x40114
# Explicit initial zero, global storage and native wrapping return-old closure.
assert word(0x609e8)==0xf90007ff;assert word(0x609f4)==0x910023e0;assert word(0x609fc)==0x900004c8;assert word(0x60a00)==0xf9039100
assert [word(a) for a in range(0x60a10,0x60a24,4)]==[0xf9400009,0x9100052a,0xf900000a,0xf9000109,0xd65f03c0]
# UInt64 metadata/witness import loads around description call.
assert pc_relative(word(0x6065c),0x6065c,True)+((word(0x60660)>>10)&4095)*8==0xe47e0
assert pc_relative(word(0x606a0),0x606a0,True)+((word(0x606a4)>>10)&4095)*8==0xe47e8
assert word(0x748d8)==0x54000241
# Original fixture from owned public Swift helper, never private ABI calls.
f=r/'tools/re/rust/canvas-core/tests/fixtures/service-identifier/swift-format.json';expected=[str(v) for v in [0,1,9,10,999,4294967296,9223372036854775808,2**64-1]];assert json.loads(f.read_text())==expected
bodies=[]
for a,b in [(0x60574,0x60710),(0x609dc,0x60a24),(0x74790,0x74a50),(0x74b00,0x74ca0)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));bodies.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
print(json.dumps({'image_sha256':pin,'uuid':m.uuid,'import_bindings':bindings,'initial_counter':0,'counter_bits':64,'returns_old_value':True,'wraps':True,'format':'UInt64.description','owned_swift_format_expected':expected,'global_counter_slot':'0xf8720','one_way_import':'0xb15c4','two_way_import':'0xb15b8','two_way_callback_thunk':'0x40114','selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'private_framework_execution_observed':False,'public_swift_format_control_executed':True,'identifier_reply_matching_proven':False,'target_settlement_proven':False},indent=2))
