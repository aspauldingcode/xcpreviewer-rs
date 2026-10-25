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
assert fields(0xd6cd4)==fields(0xd6ed8)==['title','selectionBehavior','variants','childVariantConfigurations']
assert [project(0x9e5f8,0x9e67c,i) for i in range(4)]==fields(0xd6ed8)
assert call(m,0x9e8e8)==call(m,0x9e948)==call(m,0x9e9f8)==0xb190c
assert word(0x9e8f0)==0xb4000135 and word(0x9e950)==0xb4000155 and word(0x9ea00)==0xb40001b5 and word(0x9ea8c)==0xb4000395
assert binding(m,0xe4830,8)=='__swiftEmptyArrayStorage'
assert call(m,0x9e92c)==0xa34c8 and call(m,0x9e9e0)==0x11e1c
assert word(0x9e9d4)==0x91142063
assert call(m,0x9ea6c)==call(m,0x9e7c8)==0xa3548 and call(m,0x9ea84)==0xb1948
assert word(0x9eb14)==0xb50000bc and call(m,0x9eb20)==0x49c54
assert call(m,0x9e82c)==0xb1bac
assert call(f,0xaa948)==call(f,0x9e6e4)==0x1116cc
assert call(f,0x11176c)==0x1111b0 and call(f,0x1117f0)==0xadba8
assert f.u32(f.file_offset(0x111770))==0xb4000075
assert f.u32(f.file_offset(0xadeec))==0xf9401468 and f.u32(f.file_offset(0xadf0c))==0xd63f0100
# KeyValueMap requirement table: init, subscript getter, setter, modify.
sym,ind,libs=tables(f);symbols={}
for j in range(sym[1]):
 n,k,section,d,v=f.unpack('<IBBHQ',sym[0]+16*j)
 if k&0xe==0xe and section:
  a=sym[2]+n;symbols[f.data[a:f.data.index(0,a)].decode()]=v
assert symbols['_$s22PreviewsFoundationHost11KeyValueMapPy0E0QzSg0D0QzcisTq']==0x153604
ranges=[]
for image,a,b in [(m,0x9e5f8,0x9eb64),(f,0x9e600,0x9e744),(f,0xaa850,0xaa96c),(f,0x1116cc,0x111818),(f,0xadba8,0xadfa8)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(image.path.name+'-'+hex(a)+'.s')).write_text(text)
out={'messaging_sha256':sha(m.data),'foundation_sha256':sha(f.data),'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_decoder_invoked':False,'fields':['required title:String','required SelectionBehavior','required ordered variants:[PreviewVariant]','optional recursive child dictionary defaulting to empty'],'encoding':'all four fields including empty child dictionary','dictionary_conversion':'map all key/value conversions before constructing KeyValueMap by subscript assignment; errors propagate','portable_boundary':'reject raw canonical-equivalent child keys; native Foundation-to-Swift bridging collapse is not reproduced','portable_depth_limit':64}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
