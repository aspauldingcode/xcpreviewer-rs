from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-receiver-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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
protocol=[]
for off,name in [(0xad34,'_$s16PreviewsServices0A22ServiceMessageReceiverP7receive7messageySo14UVPropertyListC_tFTj'),(0xad48,'_$s16PreviewsServices0A22ServiceMessageReceiverP7receive7message12replyHandlerySo14UVPropertyListC_yAHSg_s5Error_pSgtctFTj')]:
 names=export_names(trie,off);assert name in [x['name'] for x in names];protocol.append({'offset':hex(off),'exports':names})
expected={0x4714:0xb4000b40,0x472c:0xb4000e20,0x487c:0xf94032b3,0x4880:0xb4001b33,0x48a0:0x52800022,0x48ac:0xd73f0a71,0x4a48:0xf9401aa8,0x4a4c:0xb4000728,0x4a74:0x52800301,0x4a84:0x91004000,0x4a88:0xaa1503e1,0x4a98:0x52800401,0x4aa8:0xa9016016,0x4ac8:0xf8410e79,0x4ae0:0x91108210,0x4b08:0xd73f0b31,0x4b84:0xf9401aa8,0x4b88:0xb40003e8,0x4bb8:0xf8408d09,0x4bd0:0xd73f0931,0x8420:0xa9410e82,0xad38:0xf8408c64,0xad4c:0xf8410ca6}
for off,value in expected.items():assert word(base+off)==value
sel=selector(base+0x10340);assert sel['selector']=='initWithXpcDictionary:';assert branch(base+0x4710)==base+0x10340
assert branch(base+0x8424)==base+0x6048
assert pc_relative(word(base+0x4adc),base+0x4adc,True)+((word(base+0x4ae0)>>10)&4095)==base+0x8420
# Receiver absence is tested only after property-list/reply capability creation.
def conditional(a):
 i=word(base+a);assert i&0x7e000000==0x34000000;v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
for a,b in [(0x4714,0x487c),(0x472c,0x48f0),(0x4880,0x4be4),(0x4a4c,0x4b30),(0x4b88,0x4c04)]:assert conditional(a)==base+b
for a,b in [(0x4878,0x4a34),(0x4b40,0x4be4),(0x4c0c,0x4be4)]:assert branch(base+a)==base+b
bindings=[]
for call,name in [(0x4720,'_xpc_dictionary_create_reply'),(0x4894,'_xpc_copy_description'),(0x4a7c,'_swift_allocObject'),(0x4a8c,'_swift_weakInit'),(0x4aa0,'_swift_allocObject'),(0x4ad0,'_swift_retain'),(0x4ad8,'_swift_unknownObjectRetain')]:
 stub=branch(base+call);row=c.stub(stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names,call=hex(base+call));bindings.append(row)
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x463c,0x4c50),(0xad34,0xad5c),(0x8420,0x8428),(0x10340,0x10358)]+[(int(x['stub'],16)-base,int(x['stub'],16)-base+16) for x in bindings];regions=list(dict.fromkeys(regions));bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})

out={'services_text_sha256':sha(data),'image_uuid':uuid,'protocol':protocol,'initializer_selector':sel,'bindings':bindings,'receiver_presence_offset':48,'one_way_witness_offset':8,'request_reply_witness_offset':16,'response_thunk':'0x263308420','response_body':'0x263306048','reply_capture_bytes':32,'weak_capture_bytes':24,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'private_function_invoked':False,'exact_service_native_receiver_invoked':False,'target_settlement_proven':False}
f=artifact/'findings.json'
assert out==json.loads(f.read_text())
print('Verified',out['selected_source_bytes_verified'],'source bytes and receiver routing');work.cleanup()
