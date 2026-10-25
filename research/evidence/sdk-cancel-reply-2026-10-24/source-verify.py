from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-lifecycle-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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


trie,uuid=c.exports(base);assert uuid=='fffb683f59433c2591b272d6e5174fa3'
exports=[]
for off,suffix in [(0xa12c,'C10invalidateyyF'),(0xa230,'C4send7message12replyHandlerySo14UVPropertyListC_yAHSg_s5Error_pSgtctF'),(0x9d1c,'C19interruptionHandleryycSgvs'),(0x9fe4,'C19invalidationHandleryycSgvs')]:
 names=export_names(trie,off);assert any(x['name'].endswith(suffix) for x in names);exports.append({'offset':hex(off),'exports':names})
assert branch(base+0xa140)==base+0x37c4
# Full explicit-invalidate body clears two callbacks then nil-assigns receiver.
for a,v in [(0x39ac,0xa9440660),(0x39b0,0xa9047e7f),(0x39b8,0xa9450660),(0x39bc,0xa9057e7f),(0x39c4,0xf81a03bf),(0x39cc,0xad3c03a0),(0x39d0,0x91006260),(0x39e8,0x91006261)]:assert word(base+a)==v,(hex(a),hex(word(base+a)))
assert branch(base+0x39b4)==base+0x71b8 and branch(base+0x39c0)==base+0x71b8 and branch(base+0x39ec)==base+0x8e44
assert branch(base+0x3a2c)==base+0x3d94
# Generic helper passes backing raw object to chosen public XPC operation.
assert word(base+0x3f90)==0xf9400aa0
ops=[]
for slot,name in [(0x28f680978,'_xpc_connection_activate'),(0x28f680980,'_xpc_connection_cancel')]:
 row=data_pointer(slot);target=int(row['target'],16);path,b,e=c.image(target);t,u=c.exports(b);names=export_names(t,target-b);assert name in [x['name'] for x in names];row.update(image=path,image_uuid=u,exports=names);ops.append(row)
for a,b in [(0x3a14,0x3a18),(0x3ca4,0x3ca8)]:assert pc_relative(word(base+a),base+a,True)+((word(base+b)>>10)&4095)*8==0x28f680980
# The broader routine writes0x70, outside runtime Connection's112-byte object.
assert word(base+0x3c74)==0xa9077e7f
# Independently allocated per-reply capture and callback thunk.
for off,val in [(0x52e8,0x52800501),(0x52f4,0xa9015c15),(0x52f8,0xf900101c),(0x8e28,0xa9410a81),(0x8e2c,0xf9401283)]:assert word(base+off)==val,(hex(off),hex(word(base+off)))
assert branch(base+0x8e30)==base+0x53e0
bindings=[]
for call,name in [(0x52f0,'_swift_allocObject'),(0x5358,'__Block_copy'),(0x5368,'_swift_retain'),(0x5370,'_swift_retain'),(0x538c,'_xpc_connection_send_message_with_reply'),(0x5394,'__Block_release')]:
 stub=branch(base+call);row=c.stub(stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names,call=hex(base+call));bindings.append(row)
def rel(a):return a+struct.unpack_from('<i',data,a-base)[0]
def string(a):return c.read(a,128).split(b'\0')[0].decode()
reflection=[]
for desc,name,expected in [(0xecfc,'XPCConnection',['connection','messageReceiver','interruptionHandler','invalidationHandler','connectionErrorHandler']),(0xecc0,'XPCListener',['listenerService','service','shouldAcceptConnectionHandler','interruptionHandler','invalidationHandler','connectionErrorHandler'])]:
 a=base+desc;assert word(a)&31==16 and string(rel(a+8))==name;fd=rel(a+16);kind,size,count=struct.unpack_from('<HHI',data,fd-base+8);assert kind==1 and size==12 and count==len(expected);fields=[string(rel(fd+16+i*12+8)) for i in range(count)];assert fields==expected;reflection.append({'class':name,'descriptor':hex(a),'fields':fields})
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0xa12c,0xa150),(0x37c4,0x3a70),(0x3c58,0x3cc0),(0x3d94,0x3fdc),(0x52dc,0x53c0),(0x8e28,0x8e34),(0x71b8,0x71f8)]+[(int(x['stub'],16)-base,int(x['stub'],16)-base+16) for x in bindings];regions=list(dict.fromkeys(regions));bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
out={'services_text_sha256':sha(data),'image_uuid':uuid,'exports':exports,'operations':ops,'reply_capture_bindings':bindings,'reflection':reflection,'public_invalidate_entry':'0x2633037c4','cleared_callback_offsets':[64,80],'nil_receiver_offset':24,'connection_error_handler_no_direct_clear_offset':96,'broader_routine_owner':'Listener layout-compatible inference; not Connection invalidate','per_reply_capture_bytes':40,'per_reply_capture_offsets':[16,24,32],'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'private_connection_instantiated':False,'private_swift_abi_declared':False,'native_service_callback_invoked':False,'target_settlement_proven':False};assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes');work.cleanup()

rows=json.loads((artifact/'runtime-layout.json').read_text());assert len(rows)==4
native={x['class']:x for x in rows};image='/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices'
for row in rows:assert row['image']==image
conn=native['_TtC16PreviewsServices13XPCConnection'];assert conn['instance_size']==112 and conn['methods']==[]
assert [(x['name'],x['offset'],x['type']) for x in conn['ivars']]==[('connection',16,''),('messageReceiver',24,''),('interruptionHandler',64,''),('invalidationHandler',80,''),('connectionErrorHandler',96,'')]
listener=native['_TtC16PreviewsServices11XPCListener'];assert listener['instance_size']==128 and listener['methods']==[]
assert [(x['name'],x['offset']) for x in listener['ivars']]==[('listenerService',16),('service',24),('shouldAcceptConnectionHandler',64),('interruptionHandler',80),('invalidationHandler',96),('connectionErrorHandler',112)]
wrapper=native['_TtC16PreviewsServices25PreviewsServiceConnection'];assert wrapper['instance_size']==32 and wrapper['methods']==[]
assert [(x['name'],x['offset']) for x in wrapper['ivars']]==[('connection',16),('auditToken',24)]
last=native['_TtCC16PreviewsServices25PreviewsServiceConnection8Listener'];assert last['instance_size']==32
assert {x['selector']:x['encoding'] for x in last['methods']}=={'.cxx_destruct':'v16@0:8','init':'@16@0:8'}
print('Verified four saved owned runtime layouts; no native callback invoked')
