from pathlib import Path
import sys,struct,json,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='service-fallback-source-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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

selectors=[selector(base+x) for x in [0x10380,0x10300,0x10240]]
assert [s['selector'] for s in selectors]==['localizedDescription','initWithDictionary:','encodeToXpcDictionary:']
for call,stub in [(0x6b9c,0x10380),(0x6d24,0x10300),(0x6d3c,0x10240),(0x6c84,0x7928),(0x6944,0x7928),(0x6a1c,0x6d58),(0x66a4,0x6720)]:assert branch(base+call)==base+stub
assert word(base+0x6a08)&0xff00001f==0xb4000000
v=(word(base+0x6a08)>>5)&0x7ffff;assert base+0x6a08+4*(v-(1<<19) if v&(1<<18) else v)==base+0x6a20
assert constant(0x6c70,0x6c80,1).to_bytes(8,'little')==b'userInfo'
# The fallback writes into the original domain/code dictionary held in x27.
for off,val in [(0x6c64,0xf900427b),(0x6c88,0xf9404274),(0x6d38,0xf9400e62)]:assert word(base+off)==val,(hex(off),hex(word(base+off)))
bindings=[]
for off,name in [(0x6a04,'_xpc_dictionary_get_count'),(0x66b0,'_xpc_connection_send_message')]:
 stub=branch(base+off);row=c.stub(stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert name in [x['name'] for x in names];row.pop('raw_word');row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names,call=hex(base+off));bindings.append(row)
row=c.stub(base+0xc9d4);_,fb,_=c.image(row['target']);t,u=c.exports(fb);keys=[]
for slot,name in [(0x28f5ef708,'_NSLocalizedDescriptionKey'),(0x28f5ef468,'_NSDebugDescriptionErrorKey')]:
 row=data_pointer(slot);row['exports']=export_names(t,int(row['target'],16)-fb);assert name in [x['name'] for x in row['exports']];keys.append(row)
# Swift large-string representation uses literal address minus32; source setup
# constructs the pointer from ADRP/ADD, subtracts32, and tags its high bit.
assert pc_relative(word(base+0x6bd4),base+0x6bd4,True)+((word(base+0x6bd8)>>10)&4095)==base+0xddd0
assert word(base+0x6be0)==0xd1008108
reason=c.read(base+0xddd0,56).decode();assert reason=='Failed to encode full userInfo due to incompatible types'
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0)
section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0)
header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0)
p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x6a00,0x6d78),(0x6674,0x66bc),(0x6930,0x694c)]+[(x,x+24) for x in [0x10380,0x10300,0x10240]]+[(x,x+16) for x in [0xd134,0xd0c4]];bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True)
 (w/('source-'+hex(a)+'.s')).write_text(x.stdout)
 words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)}
 assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
out={'services_text_sha256':sha(data),'selectors':selectors,'bindings':bindings,'foundation_key_symbols':keys,'fallback_debug_reason':reason,'fallback_guard':'xpc_dictionary_get_count==0','retry_count_checked':False,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'private_function_invoked':False,'live_ipc_observed':False,'target_settlement_proven':False,'read_ranges':list(c.reads.values())}
assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes');work.cleanup()
