from pathlib import Path
import struct,subprocess,re,hashlib,json
import tempfile,sys
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
work=tempfile.TemporaryDirectory(prefix='preview-cache-verify-');w=Path(work.name)
loc={'path': '/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e.05', 'mapping_address': 9174319104, 'mapping_file_offset': 0, 'image_address': 10254024704, 'image_file_offset': 1079705600, 'bytes': 66624};base=loc['image_address']
with Path(loc['path']).open('rb') as f:
 header=f.read(32);assert header.startswith(b'dyld_');mapping_offset,mapping_count=struct.unpack_from('<II',header,16);assert mapping_count<=64
 f.seek(mapping_offset);mapping_bytes=f.read(mapping_count*32);matches=[]
 for i in range(mapping_count):
  address,size,file_offset,_,_=struct.unpack_from('<QQQII',mapping_bytes,32*i)
  if address<=base and base+loc['bytes']<=address+size:matches.append((address,file_offset,file_offset+base-address))
 assert matches==[(loc['mapping_address'],loc['mapping_file_offset'],loc['image_file_offset'])]
 f.seek(loc['image_file_offset']);data=f.read(loc['bytes'])
assert hashlib.sha256(data).hexdigest()=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
o=32;uuid=None
for _ in range(struct.unpack_from('<I',data,16)[0]):
 cmd,size=struct.unpack_from('<II',data,o)
 if cmd==0x1b:uuid=data[o+8:o+24].hex()
 o+=size
assert uuid=='fffb683f59433c2591b272d6e5174fa3'
# Original analysis-only object wrapper: native bytes unchanged, no loading/execution.
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0)
section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,45500,4096+0x16f8,2,0,0,0x80000400,0,0,0)
header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0)
p=w/'services-analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0xa20c,0xa254),(0x4e30,0x50a4),(0x50a4,0x53e0)];out=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,check=True,timeout=20);(w/('services-'+hex(a)+'.s')).write_text(x.stdout)
 words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];out.append({'offset':hex(a),'bytes':b-a,'sha256':hashlib.sha256(data[a:b]).hexdigest()})
cache_bodies=out
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');assert hashlib.sha256(m.data).hexdigest()=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
s,ind,libs=tables(m);sec=next(t for t in m.sections if t['flags']&255==8)
def binding(a):
 i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return {'symbol':m.data[o:m.data.index(0,o)].decode(),'library':libs[(d>>8)-1]}
bindings={hex(a):binding(a) for a in [0xb1888,0xb1894,0xb1c24]}
for a,text in [(0xb1888,'9contramap'),(0xb1894,'12tryContramap'),(0xb1c24,'PropertyListRepresentablePAAE08propertyE0x')]:assert text in bindings[hex(a)]['symbol']
def branch(data,offset,base):
 i=struct.unpack_from('<I',data,offset)[0];assert i>>26 in [5,0x25];v=i&0x3ffffff;return base+offset+4*(v-(1<<26) if v&(1<<25) else v)
assert branch(data,0xa220,base)==base+0x4e30;assert branch(data,0xa244,base)==base+0x50a4
for a,t in [(0x3e9a4,0xb1894),(0x3eadc,0xb1888),(0x3ec84,0x6e998),(0x3eca0,0xb1c24),(0x3f764,0x3ec20)]:assert branch(m.data,m.file_offset(a),a-m.file_offset(a))==t
assert m.u32(m.file_offset(0x1f48))==0xd65f03c0
assert pc_relative(m.u32(m.file_offset(0x3e984)),0x3e984,True)+((m.u32(m.file_offset(0x3e988))>>10)&4095)==0x3f758
assert pc_relative(m.u32(m.file_offset(0x3eac4)),0x3eac4,True)+((m.u32(m.file_offset(0x3eac8))>>10)&4095)==0x1f48
bodies=[]
for a,b in [(0x3e890,0x3e9f4),(0x3ea1c,0x3eb1c),(0x3ec20,0x3ecbc),(0x3f758,0x3f770),(0x1f48,0x1f4c)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));bodies.append({'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
foundation=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');assert hashlib.sha256(foundation.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
assert branch(foundation.data,foundation.file_offset(0x725e4),0x725e4-foundation.file_offset(0x725e4))==0xf0998
assert foundation.u32(foundation.file_offset(0xf0a90))==0x7100041f
assert foundation.u32(foundation.file_offset(0xf0a94))==0x540002e1
assert foundation.u32(foundation.file_offset(0xf0b14))==0xd63f0120
foundation_bodies=[]
for a,b in [(0x724b8,0x725fc),(0xf0998,0xf0bd4)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(foundation.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=foundation.data[foundation.file_offset(a):foundation.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));foundation_bodies.append({'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'services_text_sha256':hashlib.sha256(data).hexdigest(),'services_uuid':uuid,'cache_location':loc,'services_selected_ranges':cache_bodies,'messaging_selected_ranges':bodies,'foundation_sha256':hashlib.sha256(foundation.data).hexdigest(),'foundation_uuid':foundation.uuid,'foundation_selected_ranges':foundation_bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in cache_bodies+bodies+foundation_bodies),'typed_reply_imports':bindings,'private_functions_invoked':False,'cache_wrapper_executed':False,'services_import_labels_trusted':False,'live_ipc_observed':False,'target_settlement_proven':False},indent=2));work.cleanup()
