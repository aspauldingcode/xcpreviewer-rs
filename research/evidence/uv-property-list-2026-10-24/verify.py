from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='uv-property-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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

bindings=[]
for stub,name,call in [(0xd164,'_xpc_dictionary_set_data',0x189c),(0xd144,'_xpc_dictionary_get_data',0x1960)]:
 assert branch(base+call)==base+stub;row=c.stub(base+stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names);bindings.append(row)
selectors=[]
for call,name in [(0x1dc0,'dataWithPropertyList:format:options:error:'),(0x1e0c,'data'),(0x1b28,'propertyListWithData:options:format:error:'),(0x1c98,'dictionary'),(0x1e9c,'encodeObject:forKey:'),(0x1f0c,'decodeObjectOfClass:forKey:'),(0x1f44,'raise:format:'),(0x1fcc,'initWithXpcDictionary:'),(0x1fe4,'_encodeWithAnyCoder:'),(0x2050,'_initWithAnyCoder:')]:
 row=selector(branch(base+call));assert row['selector']==name;selectors.append(row)
assert constant(0x1db8,0x1dbc,3)==200 # Foundation binary-v1 format
# Non-null get_data pointer permits NSData construction; absence skips it.
i=word(base+0x1964);assert i&0xff00001f==0xb4000000;v=(i>>5)&0x7ffff;assert base+0x1964+4*v==base+0x1984
assert word(base+0x1dac)==0xf90007ff # NSError* initialized nil before serialization
# Both raw coder methods use the same immortal NSString key object. Its text is
# observed independently from XPC dictionary enumeration in the owned helper.
for a,b in [(0x1838,0x183c),(0x1948,0x194c),(0x1e8c,0x1e90)]:
 assert pc_relative(word(base+a),base+a,True)+((word(base+b)>>10)&4095)==0x29d491588
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x1810,0x18a0),(0x192c,0x19a4),(0x19b8,0x1ac0),(0x1ac0,0x1d78),(0x1d78,0x1e58),(0x1e58,0x1f74),(0x1f94,0x20f0)]+[(x,x+24) for x in [0x101a0,0x10180,0x103e0,0x101e0,0x10220,0x101c0,0x10400,0x10340,0x100a0,0x100c0]]+[(x,x+16) for x in [0xd164,0xd144]];bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
_,uuid=c.exports(base);assert uuid=='fffb683f59433c2591b272d6e5174fa3'
out={'services_text_sha256':sha(data),'image_uuid':uuid,'bindings':bindings,'selectors':selectors,'key_object_source_address':'0x29d491588','runtime_key':'data','selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'scope':'Owned UVPropertyList runtime methods and value/data-key projections; no native connection or target settlement','private_objc_methods_invoked':True,'private_swift_abi_declared':False,'live_ipc_observed':False,'target_settlement_proven':False,'read_ranges':list(c.reads.values())};assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes');work.cleanup()

signatures=json.loads((artifact/'signatures.json').read_text());assert signatures['class']=='UVPropertyList' and signatures['image']=='/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices'
assert signatures['instance_methods']=={'initWithDictionary:':'@24@0:8@16','initWithData:':'@24@0:8@16','data':'@16@0:8','dictionary':'@16@0:8','encodeToXpcDictionary:':'v24@0:8@16','initWithXpcDictionary:':'@24@0:8@16'}
rows=json.loads((artifact/'runtime.json').read_text());assert len(rows)==14 and all('exception' not in x for x in rows);native={x['name']:x for x in rows}
for name,size,count in [('empty',42,0),('nested',301,7),('invalid_error',0,0)]:
 row=native[name];assert row['data_bytes']==size and row['xpc_count']==1 and row['keys']==['data'] and row['all_data'] and row['payload_matches_data'] and row['decoded_count']==count and bool(row['restored'])==(name!='invalid_error')
 row=native[name+'_overwrite'];assert row['xpc_count']==2 and row['extra']==17 and row['data_type']
for name in ['missing','wrong_type','empty_data']:assert not native[name]['restored']
for name,count in [('malformed',0),('array_root',0),('xml',1)]:assert native[name]['restored'] and native[name]['decoded_count']==count
row=native['mutable_data_copy'];assert row['stored_data_follows_mutation'] and row['wire_keeps_pre_mutation_bytes'] and row['wire_differs_from_mutated_source'] and row['xpc_count']==1
assert native['copy_after_source_pool_exit']['restored'] and native['copy_after_source_pool_exit']['matches_input']
print('Verified14 owned runtime records and exact method signature profile; no native rerun')
