from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-response-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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
# The destination class reference is data, not a code address in __TEXT.
destination=data_pointer(0x28f5efc10);target=int(destination['target'],16);foundation=0x181d9e000;t,u=c.exports(foundation);names=export_names(t,target-foundation);assert '_OBJC_CLASS_$_NSError' in [x['name'] for x in names]
owner=None;current=None
for line in (c.root/'dyld_shared_cache_arm64e.map').read_text().splitlines():
 if line.startswith('/'):current=line
 values=re.findall('0x[0-9A-Fa-f]+',line)
 if current and len(values)==2 and int(values[0],16)<=target<int(values[1],16):assert owner is None;owner=current
assert owner=='/System/Library/Frameworks/Foundation.framework/Versions/C/Foundation'
destination.update(image=owner,image_base=hex(foundation),image_uuid=u,exports=names)
# Weak owner first, then nullable payload before error. Verify source registers.
for off,value in [(0x6134,0x910042c0),(0x6148,0x910042c0),(0x6154,0xaa0003f6)]:assert word(base+off)==value
# Class reference for the dynamic cast is obtained via the checked metadata helper.
assert pc_relative(word(base+0x6304),base+0x6304,True)+((word(base+0x6308)>>10)&4095)==0x28f5efc10
assert branch(base+0x6310)==base+0x8428
assert word(base+0x6324)==0x528000c4 # dynamic cast flags6; not a guessed prototype
assert word(base+0x66a8)==0xf9400ac0 # backing raw connection
assert branch(base+0x66a4)==base+0x6720
selector_stub=branch(base+0x64b0);sel=selector(selector_stub);assert sel['selector']=='encodeToXpcDictionary:'
def conditional(a):
 i=word(base+a);assert i&0x7e000000==0x34000000;v=(i>>5)&0x7ffff;return base+a+4*(v-(1<<19) if v&(1<<18) else v)
for a,b in [(0x6150,0x6654),(0x6158,0x62d4),(0x62d4,0x64e4)]:assert conditional(a)==base+b
inst=word(base+0x632c);assert inst&0x7f000000==0x36000000;v=(inst>>5)&0x3fff;assert base+0x632c+4*(v-(1<<14) if v&(1<<13) else v)==base+0x64e4
bindings=[]
for call,name in [(0x6144,'_swift_beginAccess'),(0x614c,'_swift_weakLoadStrong'),(0x6328,'_swift_dynamicCast'),(0x64c4,'_xpc_connection_send_message'),(0x66b0,'_xpc_connection_send_message'),(0x8450,'_objc_opt_self'),(0x8454,'_swift_getObjCClassMetadata')]:
 stub=branch(base+call);row=c.stub(stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names,call=hex(base+call));bindings.append(row)
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x6048,0x6720),(0x8428,0x8470),(selector_stub-base,selector_stub-base+24)]+[(int(x['stub'],16)-base,int(x['stub'],16)-base+16) for x in bindings];regions=list(dict.fromkeys(regions));bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})

out={'services_text_sha256':sha(data),'image_uuid':uuid,'destination_class':destination,'bindings':bindings,'payload_encoder':sel,'weak_owner_gate':'0x263306150','payload_gate':'0x263306158','nil_error_gate':'0x2633062d4','failed_cast_branch':'0x26330632c','send_calls':['0x2633064c4','0x2633066b0'],'error_encoder':'0x263306720','selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'native_private_response_invoked':False,'target_settlement_proven':False}
f=artifact/'findings.json'
assert out==json.loads(f.read_text())
print('Verified',out['selected_source_bytes_verified'],'source bytes and NSError destination metadata');work.cleanup()
