from pathlib import Path
import sys,struct,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
from reloop.discriminants import pc_relative
import tempfile
artifact=Path(__file__).parent;work=tempfile.TemporaryDirectory(prefix='reply-error-verify-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
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
selectors=[selector(base+0x101e0),selector(base+0x10320)];assert [s['selector'] for s in selectors]==['dictionary','initWithDomain:code:userInfo:']
_,swiftbase,_=c.image(0x193bb59d0);trie,uuid=c.exports(swiftbase);metadata=[]
for slot,name in [(0x28f67ca90,'_$sSSN'),(0x28f67ce98,'_$sSiN')]:
 row=data_pointer(slot);row['exports']=export_names(trie,int(row['target'],16)-swiftbase);assert name in [x['name'] for x in row['exports']];metadata.append(row)
a=base+0xd828;off,length=struct.unpack('<iI',c.read(a,8));assert length==8 and c.read(a+off,length)==b'SDySSypG'
def short(a,b):
 regs=[0,0]
 for pc in range(a,b,4):
  i=word(pc);d=i&31;assert d in [0,1];sf=i>>31;width=64 if sf else 32;shift=((i>>21)&3)*16;v=((i>>5)&65535)<<shift
  if i&0x7f800000==0x52800000:regs[d]=v
  elif i&0x7f800000==0x72800000:regs[d]=(regs[d]&~(65535<<shift))|v
  else:raise AssertionError('String constant instruction changed')
  regs[d]&=(1<<width)-1
 return (regs[0].to_bytes(8,'little')+regs[1].to_bytes(8,'little'))[:(regs[1]>>56)&15].decode()
keys=[short(base+a,base+b) for a,b in [(0x5e48,0x5e58),(0x5ea0,0x5eac),(0x5ef0,0x5f04)]];assert keys==['domain','code','userInfo']
assert branch(base+0x5e04)==base+0x101e0;assert branch(base+0x5fb8)==base+0x10320;assert branch(base+0x5a48)==base+0x5ddc
for off,val in [(0x5a4c,0xb4000bc0),(0x5e74,0xf9454863),(0x5ec8,0xf9474c63),(0x5d0c,0xd2800000),(0x5d10,0xaa1303e1),(0x5d74,0xaa1503e0),(0x5d78,0xd2800001)]:assert word(base+off)==val
bindings=[]
for stub,expected in [(0xc9b4,'Dictionary'),(0xce84,'_swift_dynamicCast'),(0xc9a4,'Dictionary'),(0xc9c4,'String'),(0xcec4,'_swift_getObjCClassFromMetadata')]:
 row=c.stub(base+stub);path,b,e=c.image(row['target']);t,u=c.exports(b);names=export_names(t,row['target']-b);assert names;row.update(target=hex(row['target']),image=path,image_uuid=u,exports=names);row.pop('raw_word');bindings.append(row)
assert '_swift_dynamicCast' in [x['name'] for x in bindings[1]['exports']]
# Original non-executed analysis wrapper; native bytes unchanged.
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,len(data)-0x16f8,4096+0x16f8,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);p=w/'analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x5ddc,0x6048),(0x5a40,0x5a50),(0x5d0c,0x5d20),(0x5d74,0x5d88),(0x7164,0x71b8),(0x101e0,0x101f8),(0x10320,0x10338)]+[(x,x+16) for x in [0xc9b4,0xce84,0xc9a4,0xc9c4,0xcec4]];bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,timeout=20,check=True);(w/('source-'+hex(a)+'.s')).write_text(x.stdout);words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':sha(data[a:b])})
native=json.loads((artifact/'coercions.json').read_text());assert native=={'above_real_max':str(2**63-1),'bool':'1','false':'0','fraction':None,'high_next_up':None,'huge_real':None,'infinity':None,'integer':'-17','integral_real':'3','low_next_down':None,'max_integer':str(2**63-1),'min_integer':str(-2**63),'min_real':str(-2**63),'nan':None,'negative_zero':'0','string':None,'uint64_max':None}
expected=''.join(k+'\t'+('none' if v is None else v)+'\n' for k,v in sorted(native.items()) if k!='uint64_max');assert (r/'tools/re/rust/canvas-core/tests/fixtures/service-reply-error/coercions.tsv').read_text()==expected
out={'services_text_sha256':sha(data),'keys':keys,'selectors':selectors,'metadata':metadata,'user_info_mangled_type':'SDySSypG','swift_core_uuid':uuid,'bindings':bindings,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies),'public_swift_casts':native,'representable_fixture_cases':16,'private_function_invoked':False,'live_ipc_observed':False,'target_settlement_proven':False,'read_ranges':list(c.reads.values())};assert out==json.loads((artifact/'findings.json').read_text());print('Verified',out['selected_source_bytes_verified'],'source bytes; fields/types/selectors and public Swift casts');work.cleanup()
