from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-connection-event-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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

# Weak owner gate, actual type check, category routing and optional handler slots.
expected={0x40d8:0x91004260,0x40e0:0xb40027e0,0x40f8:0xeb14001f,0x40fc:0x540011c0,0x44a8:0x72001f48,0x44ac:0x54000320,0x44b0:0x71000d1f,0x44b4:0x54000061,0x44b8:0xaa1802e8,0x44bc:0xb40006a8,0x44c0:0xf9403275,0x44c4:0xb40005f5,0x44c8:0xf9403674,0x44d4:0xaa1703e0,0x44d8:0xaa1803e1,0x44dc:0xaa1a03e2,0x44e4:0xd73f0ab1,0x4510:0xf9402a75,0x4514:0xb4000595,0x4528:0xd73f0ab1,0x4590:0xf9402275,0x4594:0xb4000215,0x45a8:0xd73f0ab1,0x7c9c:0xaa0003f3,0x7cc8:0x52800301,0x7cd8:0x91004000,0x7cdc:0xaa1403e1,0x7ce8:0x910bd210,0x7cf4:0xa90257f0,0x7d28:0x91340210,0x7d5c:0xaa1303e0,0x7d60:0xaa1503e1,0x82f4:0xaa1403e1,0x8540:0xd2800001}
for off,value in expected.items():assert word(base+off)==value
# Offset0x10 of the allocated24-byte capture is Swift weak storage.
assert pc_relative(word(base+0x7ce4),base+0x7ce4,True)+((word(base+0x7ce8)>>10)&4095)==base+0x82f4
assert pc_relative(word(base+0x7d24),base+0x7d24,True)+((word(base+0x7d28)>>10)&4095)==base+0x3d00
assert branch(base+0x82f8)==base+0x4000
assert branch(base+0x411c)==base+0x8004
# Conditional destinations distinguish absent specialized handlers from fallback.
def conditional(a):
 i=word(base+a);assert i&0xff000010==0x54000000 or i&0x7e000000==0x34000000
 v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
for a,b in [(0x40e0,0x45dc),(0x40fc,0x4334),(0x44ac,0x4510),(0x44b4,0x44c0),(0x44bc,0x4590),(0x44c4,0x4580),(0x4514,0x45c4),(0x4594,0x45d4)]:assert conditional(a)==base+b
for a,b in [(0x450c,0x45dc),(0x4544,0x45b4),(0x45c0,0x45dc),(0x458c,0x45d0)]:assert branch(base+a)==base+b
bindings=[]
for call,name in [(0x7cd0,'_swift_allocObject'),(0x7ce0,'_swift_weakInit'),(0x7d40,'__Block_copy'),(0x7d50,'_swift_unknownObjectRetain'),(0x7d58,'_swift_release'),(0x7d64,'_xpc_connection_set_event_handler'),(0x7d6c,'__Block_release'),(0x40d4,'_swift_beginAccess'),(0x40dc,'_swift_weakLoadStrong'),(0x40ec,'_xpc_get_type'),(0x40f4,'_$s3XPC0A16_TYPE_DICTIONARYs13OpaquePointerVvg'),(0x3d20,'_swift_retain'),(0x3d28,'_swift_unknownObjectRetain'),(0x3d38,'_swift_release'),(0x8548,'_xpc_connection_create_mach_service')]:
 stub=branch(base+call);row=c.stub(stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names,call=hex(base+call));bindings.append(row)
# SDK declaration pins targetq as the second argument, not a runtime queue ID.
header=Path('/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/xpc/connection.h');sdk=header.read_bytes();assert b'dispatch_queue_t _Nullable targetq, uint64_t flags);' in sdk
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x4000,0x463c),(0x7c84,0x7d88),(0x3d00,0x3d60),(0x82f4,0x82fc),(0x8534,0x857c)]+[(int(x['stub'],16)-base,int(x['stub'],16)-base+16) for x in bindings];regions=list(dict.fromkeys(regions));bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})


out={'services_text_sha256':sha(data),'image_uuid':uuid,'enum_fields':fields,'bindings':bindings,'weak_capture_bytes':24,'weak_storage_offset':16,'event_entry':'0x263304000','specialized_notification_slots':[64,80],'other_error_slot':96,'missing_specialized_falls_back':False,'source_mach_service_target_queue_argument':None,'sdk_header_sha256':sha(sdk),'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'native_callback_invoked':False,'native_queue_observed':False,'target_settlement_proven':False}
f=artifact/'findings.json'
assert out==json.loads(f.read_text())
print('Verified',out['selected_source_bytes_verified'],'source bytes and event installation/routing');work.cleanup()
