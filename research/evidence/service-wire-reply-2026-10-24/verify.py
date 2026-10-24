from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-wire-reply-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
def word(a):return struct.unpack_from('<I',data,a-base)[0]
def branch(a):
 i=word(a);assert i>>26 in [5,0x25];v=i&0x3ffffff;return a+4*(v-(1<<26) if v&(1<<25) else v)
def data_pointer(slot):
 lo,hi,o,p=next(m for m in c.maps if m[0]<=slot and slot+8<=m[1])
 with p.open('rb') as f:
  h=f.read(0x160);mo,mc=struct.unpack_from('<II',h,0x138);assert mc<=64;f.seek(mo);d=f.read(mc*56);rows=[struct.unpack_from('<6QII',d,i*56) for i in range(mc)];rows=[m for m in rows if m[0]<=slot and slot+8<=m[0]+m[1]];assert len(rows)==1
  a,size,fo,so,ss,flags,mp,ip=rows[0];assert (a,fo)==(lo,o);f.seek(so);meta=f.read(24);version,ps,count,add=struct.unpack('<III4xQ',meta);assert version==5 and ps in (4096,16384) and count*2+24<=ss;pi=(slot-a)//ps;assert pi<count;f.seek(so+24+pi*2);first=struct.unpack('<H',f.read(2))[0];assert first!=65535
 origin=a+pi*ps;page=c.read(origin,ps);cursor=first
 for hops in range(ps//8):
  assert 0<=cursor<=ps-8;v=struct.unpack_from('<Q',page,cursor)[0]
  if cursor==slot-origin:break
  step=(v>>52)&2047;assert step and cursor<slot-origin;cursor+=8*step
 else:raise AssertionError('chain limit')
 assert not v>>63 and not (v>>42)&1023
 target=(add+(v&((1<<34)-1)))|(((v>>34)&255)<<56)
 return {'slot':hex(slot),'target':hex(target),'chain_hops':hops,'page_start_bytes':first,'page_origin':hex(origin),'page_size':ps,'profile':'v5 regular','cache_uuid':h[88:104].hex(),'slide_header_sha256':sha(meta)}
def selector(a):
 i,j=word(a),word(a+4);assert i&0x9f00001f==0x90000001 and j&0xffc003ff==0xf9400021
 slot=pc_relative(i,a,True)+((j>>10)&4095)*8;row=data_pointer(slot);s=c.read(int(row['target'],16),128).split(b'\0')[0].decode();return row|{'selector':s,'stub':hex(a)}


assert branch(base+0x5e04)==base+0x101e0;assert selector(base+0x101e0)['selector']=='dictionary'
assert branch(base+0x5a48)==base+0x5ddc
assert word(base+0x5a4c)==0xb4000bc0
for off,val in [(0x5d0c,0xd2800000),(0x5d10,0xaa1303e1),(0x5d74,0xaa1503e0),(0x5d78,0xd2800001)]:assert word(base+off)==val
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
bodies=[]
for a,b in [(0x5a08,0x5a50),(0x5d0c,0x5d20),(0x5d74,0x5d88),(0x5e00,0x5e08),(0x101e0,0x101f8)]:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('services-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'image':'PreviewsServices','offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
def mw(a):return m.u32(m.file_offset(a))
def mb(a):
 i=mw(a);assert i>>26 in [5,0x25];v=i&0x3ffffff;return a+4*(v-(1<<26) if v&(1<<25) else v)
symbols,ind,libs=tables(m);sec=next(t for t in m.sections if t['flags']&255==8)
def imported(a):
 i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',symbols[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=symbols[2]+n;return {'symbol':m.data[o:m.data.index(0,o)].decode(),'library':libs[(d>>8)-1]}
imports={hex(a):imported(a) for a in [0xb22c0,0xb1558,0xb1930]}
for a,part in [(0xb22c0,'_stdlib_isOSVersionAtLeast'),(0xb1558,'DataV36_unconditionallyBridgeFromObjectiveC'),(0xb1930,'PropertyListV22serializableDictionary')]:assert part in imports[hex(a)]['symbol']
def defined(a,name):
 found=[]
 for i in range(symbols[1]):
  n,k,ss,d,v=m.unpack('<IBBHQ',symbols[0]+16*i)
  if v==a and k&0xe==0xe and n<symbols[3]:
   o=symbols[2]+n;found.append(m.data[o:m.data.index(0,o)].decode())
 assert name in found
 return {'address':hex(a),'defined_symbol':name}
selectors=[defined(0xb28e0,'_objc_msgSend$data'),defined(0xb2960,'_objc_msgSend$dictionary')]
for a,b in [(0x3fd34,0xb22c0),(0x3fd4c,0xb28e0),(0x3fee8,0xb2960),(0x3fd5c,0xb1558),(0x3ff2c,0xb1930)]:assert mb(a)==b
for a,v in [(0x3fd28,0x528001c0),(0x3fd2c,0x52800081),(0x3fd30,0xd2800002),(0x3fd80,0x52800022),(0x3ff3c,0x52800002)]:assert mw(a)==v
# TBZ on version result selects dictionary at3fee8; byte path is fallthrough.
i=mw(0x3fd48);assert i&0xfff8001f==0x36000018;v=(i>>5)&16383;assert 0x3fd48+4*v==0x3fee8
fd=m.relative(0xd1648+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert (kind,size,n)==(2,12,2);cases=[m.string(m.relative(fd+16+i*size+8)) for i in range(n)];assert cases==['deserialized','serialized']
for a,b in [(0x3fcb8,0x3fd88),(0x3fee8,0x3ff40),(0xb28e0,0xb28f4),(0xb2960,0xb2974)]:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,timeout=20,check=True);(w/('messaging-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert b''.join(words[i] for i in range(a,b,4))==raw;bodies.append({'image':'PreviewsMessagingHost','offset':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'services_text_sha256':sha(data),'messaging_image_sha256':sha(m.data),'messaging_uuid':m.uuid,'messaging_imports':imports,'messaging_defined_selectors':selectors,'lazy_cases':cases,'serialized_mode_gate':[14,4,0],'original_uv_object_passed_on_nonerror':True,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'private_swift_abi_declared':False,'native_service_callback_invoked':False,'live_ipc_observed':False,'target_settlement_proven':False};assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes across both images');work.cleanup()

native=json.loads((artifact/'runtime.json').read_text());assert native=={'bytes':280,'class_image':'/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices','complete_fields_match':True,'restored':1,'serialized_bytes_preserved':True,'xpc_count':1}
fixture=r/'tools/re/rust/canvas-core/tests/fixtures/service-wire-reply/remote-error.wire-data';assert len(fixture.read_bytes())==native['bytes']
print('Verified saved owned UVPropertyList error fixture observation; no native rerun')
