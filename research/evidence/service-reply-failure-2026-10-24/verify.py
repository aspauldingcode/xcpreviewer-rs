from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-reply-failure-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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
def eq(a):
 i=word(base+a);assert i&0xff00001f==0x54000000;v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
assert eq(0x5508)==base+0x5790 and branch(base+0x552c)==base+0x8004
assert eq(0x8030)==base+0x8058
for a,b in [(0x8078,0x8094),(0x80b4,0x80e0),(0x80c0,0x8148),(0x8100,0x811c),(0x812c,0x8170),(0x5a10,0x5b68)]:assert cb(a)==base+b
for a,b in [(0x8054,0x8194),(0x8090,0x8194),(0x80dc,0x8194),(0x8118,0x8194),(0x816c,0x8194)]:assert branch(base+a)==base+b
for a,value in [(0x8050,1),(0x808c,3),(0x80d8,0),(0x8110,3),(0x8190,2)]:assert constant(a,a+4,2)==value
assert constant(0x8084,0x8088,20)==0 and constant(0x8114,0x8118,20)==1
assert constant(0x5ba0,0x5ba4,8)==1 and constant(0x5ba8,0x5bac,0)==0
assert constant(0x5990,0x5994,0)==0 # non-dictionary callback has no payload
sel=selector(base+0x10340);assert sel['selector']=='initWithXpcDictionary:';assert branch(base+0x5a08)==base+0x10340
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
bindings=[]
for stub,name in [(0xd184,'_xpc_get_type'),(0xc934,'_$s3XPC0A16_TYPE_DICTIONARYs13OpaquePointerVvg'),(0xc914,'_$s3XPC0A11_TYPE_ERRORs13OpaquePointerVvg'),(0xd104,'_xpc_copy_description'),(0xc974,'_$s3XPC0A29_ERROR_CONNECTION_INTERRUPTEDSo13OS_xpc_object_pvg'),(0xc954,'_$s3XPC0A25_ERROR_CONNECTION_INVALIDSo13OS_xpc_object_pvg'),(0xc964,'_$s3XPC0A27_ERROR_TERMINATION_IMMINENTSo13OS_xpc_object_pvg'),(0xd174,'_xpc_equal'),(0xd084,'_xpc_connection_copy_invalidation_reason'),(0xc944,'_$s3XPC0A22_ERROR_KEY_DESCRIPTIONSPys4Int8VGvg'),(0xd154,'_xpc_dictionary_get_string')]:
 row=c.stub(base+stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names);bindings.append(row)
for call,stub in [(0x54f4,0xd184),(0x54fc,0xc934),(0x8020,0xd184),(0x8028,0xc914),(0x8038,0xd104),(0x8058,0xc974),(0x8068,0xd174),(0x8094,0xc954),(0x80a4,0xd174),(0x80bc,0xd084),(0x80e0,0xc964),(0x80f0,0xd174),(0x811c,0xc944),(0x8128,0xd154),(0x5b6c,0xd104)]:assert branch(base+call)==base+stub
assert c.read(base+0xde10,16)==b'<no description>'
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x8004,0x81ac),(0x54f0,0x5544),(0x59f8,0x5a50),(0x5b68,0x5bc4),(0x5968,0x59ac),(0x10340,0x10358)]+[(x,x+16) for x in [0xd184,0xc934,0xc914,0xd104,0xc974,0xc954,0xc964,0xd174,0xd084,0xc944,0xd154]];bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
out={'services_text_sha256':sha(data),'enum_fields':fields,'enum_descriptor':hex(kind),'field_descriptor':hex(fd),'selector':sel,'bindings':bindings,'absent_description':'<no description>','selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'scope':'Projected callback classification only; native handlers and invalidation side effects excluded','private_function_invoked':False,'live_ipc_observed':False,'target_settlement_proven':False,'read_ranges':list(c.reads.values())};assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes');work.cleanup()
