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

p=MachO(base/'PreviewsPipeline.framework/Versions/A/PreviewsPipeline');assert sha(p.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
def pw(a):return p.u32(p.file_offset(a))
def pf(a):
 kind,size,n=p.unpack('<HHI',p.file_offset(a+8));assert size==12;return [p.string(p.relative(a+16+i*size+8)) for i in range(n)]
assert pf(0x557058)==['live','grid','static'] and pf(0x55978c)==['isEnabled','selection']
assert pf(0x559710)[5]=='overrides' and pw(0x2b7da4)==0xb9802408
assert pw(0x2b70f8)==0x39000100 and pw(0x2b70fc)==0xf9000501
assert call(p,0x2b7efc)==0xe297c and pw(0x2b7f04)==0x3607f981 and pw(0x2b7f30)==0x360051d4
assert pw(0x2b7ff0)==0x7100041f and pw(0x2b80bc)==0x36000173
assert call(p,0x2b8024)==call(p,0x2b803c)==0x51e044
assert binding(p,0x51e044)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV2idAC2IDVvg'
assert binding(p,0x51f8bc)=='_$sSQ2eeoiySbx_xtFZTj'
assert pw(0x16c678)==0x710006df and pw(0x16c67c)==0x54000101
# Grid is the associated PreviewVariantGroup payload. Static has no associated type.
e=0x557058+16+12;typ=p.relative(e+4);assert typ==0x5490e2 and p.data[p.file_offset(typ)]==2
slot=typ+1+p.unpack('<i',p.file_offset(typ+1))[0];assert binding(p,slot,8)=='_$s21PreviewsMessagingHost19PreviewVariantGroupVMn'
assert p.relative(0x557058+16+24+4) is None
assert call(p,0x2b80f8)==0x51e014 and pw(0x2b8124)==0x54000221
assert call(p,0x2b818c)==call(p,0x2b85d4)==0x51e368
assert binding(p,0x51e368)=='_$s21PreviewsMessagingHost29PreviewOverridesConfigurationV8variantsSayAA0D7VariantVGvg'
assert pw(0x2b8328)==0x37000133 and pw(0x2b8748)==0x37000133
assert pw(0x2b841c)==0xf9400808 and pw(0x2b8444)==0xf8100128 and pw(0x2b84c8)==0xf8500108
assert call(p,0x2b8538)==0x51e35c and call(p,0x2b855c)==0xe2c74 and pw(0x2b8560)==0x3607f941
assert call(p,0x2b8830)==0x55570
# Complete function direct calls contain no recursive call to itself/defaultSelection.
calls=[]
for a in range(0x2b7988,0x2b8a20,4):
 if pw(a)>>26==37:calls.append(call(p,a))
assert 0x2b7988 not in calls
ranges=[]
for a,b in [(0x2b7988,0x2b8a20),(0x2b70f8,0x2b7104),(0x16c5fc,0x16c6cc)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(hex(a)+'.s')).write_text(text)
out={'image_sha256':sha(p.data),'uuid':p.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_selection_method_invoked':False,'semantics':'require enabled settings and override config; exclude grid associated group by canonical ID; filter direct variants using selection; iterate fixed direct-result snapshot and append selected immediate child variants; no grandchildren/default selection/association lookup/dedup','native_selection_or_transport_proven':False}
q=w/'source-findings.json'
if q.exists():assert out==json.loads(q.read_text())
else:q.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
