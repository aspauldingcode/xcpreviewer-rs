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
  else:raise AssertionError((hex(a),hex(i),'outside bounded getter instruction subset'))
  if d!=31:regs[d]=v&mask
 else:raise AssertionError('No getter return')
 lo,hi=regs[:2]
 if lo>>60==13:
  length=lo&((1<<48)-1);address=(hi&((1<<63)-1))+32;assert length<=64;off=m.file_offset(address);return m.data[off:off+length].decode()
 length=(hi>>56)&15;return (lo.to_bytes(8,'little')+hi.to_bytes(8,'little'))[:length].decode()
assert fields(0xd3cb8)==fields(0xd3ec4)==['pid','contentIdentifier','updateSeed']
assert [project(0x2530c,0x25368,i) for i in range(3)]==fields(0xd3ec4)
assert project(0x60898,0x608b8,8)=='cancelUpdate'
assert fields(0xd4ec0)[8]==fields(0xd4f78)[6]=='cancelUpdate'
assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a+16))[0]==0x6029c
assert 0x5e96c+4*m.data[m.file_offset(0xba16d)+6]==0x5eca4
assert call(m,0x602c0)==0x5ef5c and call(m,0x602e0)==0xb1c24 and word(0x60494)==0x528000c2
assert call(m,0x5ecbc)==0x5ef5c and call(m,0x5ecd8)==0xb1c18
assert call(m,0x25504)==call(m,0x25544)==call(m,0x255c8)==0xb190c
assert word(0x2550c)==0xb5000235 and word(0x2554c)==0xb4000255
assert call(m,0x25528)==0x24070 and call(m,0x255ac)==0x23fb0
assert binding(m,0xe4758,8)=='_$ss5Int32VN'
assert word(0x5ba4)==0xf9400280 and word(0x5ba8)==0xd65f03c0 and word(0x1b6e0)==0xf9000100 and word(0x1b6e4)==0xd65f03c0
def address(name):
 table,_,_=tables(m);symoff,count,stroff,size=table
 for i in range(count):
  n,k,ss,d,value=m.unpack('<IBBHQ',symoff+16*i);o=stroff+n
  if m.data[o:m.data.index(0,o)].decode()==name:return value
 raise AssertionError(name)
assert address('_$s21PreviewsMessagingHost0C10UpdateSeedV17propertyListValues6UInt64Vvg')==0x5ba4
assert address('_$s21PreviewsMessagingHost0C10UpdateSeedV17propertyListValueACs6UInt64V_tKcfC')==0x1b6e0
assert call(m,0x36b14)==0x36360 and call(m,0x365bc)==0xb1c30 and call(m,0x3660c)==0xb1c3c
regions=[('Messaging',m,0x2530c,0x25618),('Messaging',m,0x6029c,0x602ec),('Messaging',m,0x60460,0x6049c),('Messaging',m,0x5eca4,0x5ece4),('Messaging',m,0x5ba4,0x5bac),('Messaging',m,0x1b6e0,0x1b6e8),('Messaging',m,0x36578,0x36624),('Messaging',m,0x36360,0x36378),('Messaging',m,0x60898,0x608b8)]
ranges=[]
for name,image,a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(name+'-'+hex(a)+'.s')).write_text(text)
out={'image_sha256':sha(m.data),'uuid':m.uuid,'fields':['pid','contentIdentifier','updateSeed'],'pid_type':'Int32','content_type':'String raw-representable','seed_type':'UInt64','wire_kind':'cancelUpdate','decoder_failures_propagate':True,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_decoder_invoked':False,'native_cancellation_performed':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
