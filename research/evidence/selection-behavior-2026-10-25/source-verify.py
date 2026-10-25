from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
sha=lambda b:hashlib.sha256(b).hexdigest();base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');m=MachO(base/'PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO(base/'PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c' and sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(image,a):
 v=image.u32(image.file_offset(a));assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def fields(a):
 kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
def binding(image,a,stride=12):
 s,ind,libs=tables(image);sec=next(t for t in image.sections if t['address']<=a<t['address']+t['size']);i=index(image,sec,a,stride,ind);n,k,ss,d,v=image.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return image.data[o:image.data.index(0,o)].decode()
def project(start,end,tag):
 regs=[0]*32;comparison=0
 for a in range(start,end,4):
  i=m.u32(m.file_offset(a));d=i&31;n=(i>>5)&31;sf=i>>31;mask=(1<<(64 if sf else 32))-1
  if i==0xd65f03c0:break
  if i&0xffc00000==0x39400000:assert n==20;v=tag
  elif i&0x7f800000==0x52800000:v=((i>>5)&65535)<<(((i>>21)&3)*16)
  elif i&0x7f800000==0x72800000:
   sh=((i>>21)&3)*16;v=(regs[d]&~(65535<<sh))|(((i>>5)&65535)<<sh)
  elif i&0x9f000000==0x90000000:v=pc_relative(i,a,True)
  elif i&0x7f00001f==0x7100001f:comparison=regs[n]-((i>>10)&4095);continue
  elif i&0x7f000000 in [0x11000000,0x51000000]:
   v=regs[n]+(-1 if i&(1<<30) else 1)*(((i>>10)&4095)<<(12 if i&(1<<22) else 0))
  elif i&0x7f200000==0x2a000000:
   assert (i>>22)&3==0;v=regs[n]|(regs[(i>>16)&31]<<((i>>10)&63))
  elif i&~0x3ff==0xb2410000:v=regs[n]|(1<<63)
  elif i==0xb240018c:v=regs[n]|1
  elif i&0x7fe00c00==0x1a800000:
   condition=(i>>12)&15;assert condition in [0,12];yes=comparison==0 if condition==0 else comparison>0;v=regs[n] if yes else regs[(i>>16)&31]
  elif i==0xa9002909:regs[0]=regs[9];regs[1]=regs[10];continue
  else:raise AssertionError((hex(a),hex(i),'outside bounded getter instruction subset'))
  if d!=31:regs[d]=v&mask
 else:raise AssertionError('No getter return')
 lo,hi=regs[:2]
 if lo>>60==13:
  length=lo&((1<<48)-1);address=(hi&((1<<63)-1))+32;assert length<=64;off=m.file_offset(address);return m.data[off:off+length].decode()
 length=(hi>>56)&15;return (lo.to_bytes(8,'little')+hi.to_bytes(8,'little'))[:length].decode()
assert call(m,0x9fe38)==0x1b44
assert binding(m,0xb220c)=='_$ss21_findStringSwitchCase5cases6stringSiSays06StaticB0VG_SStF'
assert word(0x1b98)==0xf100067f and word(0x1ba0)==0x1a880508 and word(0x1ba8)==0x1a8803e8
assert fields(0xd6d64)==fields(0xd6d8c)==['singleSelect','multiSelect']
assert fields(0xd6f68)==['discriminant','singleSelectConfiguration','multiSelectConfiguration']
assert [project(0x9fe3c,0x9fe88,i) for i in range(2)]==fields(0xd6d8c)
assert [project(0xa03ac,0xa041c,i) for i in range(3)]==fields(0xd6f68)
assert call(m,0xa0628)==0xa3798 and call(m,0xa0644)==0xb190c and word(0xa064c)==0xb4000235
assert word(0xa069c)==0x7100051f and word(0xa06a0)==0x54000381
assert word(0xa06a8)==0x52800048 and call(m,0xa06b0)==0xa37d8 and call(m,0xa06cc)==0xb190c
assert word(0xa0714)==0x52800028 and call(m,0xa071c)==0xa3818 and call(m,0xa0738)==0xb190c
assert word(0xa06f8)==0xb5fffbf3 and word(0xa0764)==0xb5fff893
assert call(m,0xa04a8)==call(m,0xa0564)==0xa3798
assert call(m,0xa04b0)==0xa3818 and call(m,0xa056c)==0xa37d8
assert call(m,0xa04f8)==call(m,0xa05b4)==0xb1bc4
# New pending dependency: recursive dictionary, not a child array.
assert call(m,0x9ea6c)==0xa3548 and call(m,0x9ea84)==0xb1948
sym,ind,libs=tables(m);symbols={}
for j in range(sym[1]):
 n,k,section,d,v=m.unpack('<IBBHQ',sym[0]+16*j)
 if k&0xe==0xe and section:
  a=sym[2]+n;symbols[m.data[a:m.data.index(0,a)].decode()]=v
assert symbols['_$sSDy21PreviewsMessagingHost14PreviewVariantV2IDVAA0D22OverridesConfigurationVGSDyxq_G0a10FoundationC025PropertyListRepresentableA2jKRzAjKR_SH0jK5ValueAjKPRpzrlWl']==0xa3548
regions=[(0x1b44,0x1bc0),(0x9fe30,0x9fe88),(0xa03ac,0xa0784),(0x9ea4c,0x9ea90)]
ranges=[]
for a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(hex(a)+'.s')).write_text(text)
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_decoder_invoked':False,'selection_or_rendering_performed':False,'discriminants':['singleSelect','multiSelect'],'keys':['discriminant','singleSelectConfiguration','multiSelectConfiguration'],'routing':'required closed discriminant first; require only selected payload; selected errors propagate without fallback','encoding':'discriminant plus only active configuration','pending_child_dependency':'childVariantConfigurations optional Dictionary<PreviewVariant.ID,PreviewOverridesConfiguration>; recursive, not an array; duplicate canonical key and nested failure semantics unqualified'}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
