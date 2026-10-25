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

assert word(0x9dea0)==0xf9401288 and word(0x9dea8)==0xf9402680
assert word(0x9dee4)==0xf9403288 and word(0x9deec)==0xf9403693
assert word(0x9df2c)==0x9100635a and word(0x9df44)==0xf9400357
assert word(0x9dfc0)==0x52800608 and call(m,0x9dfd8)==0xb2518
assert call(m,0x9e104)==0x9dec8 and call(m,0x9e110)==0xb0c4
assert call(m,0x9e13c)==0xa3420 and call(m,0x9e17c)==0xb15f4
assert binding(m,0xb15f4)=='_$s22PreviewsFoundationHost10OrderedSetVyACyxGqd__c7ElementQyd__RszSTRd__lufC'
assert call(m,0x9e1b0)==0xb1eb8 and binding(m,0xb1eb8)=='_$sST22_copyToContiguousArrays0cD0Vy7ElementQzGyFTj'
assert call(m,0xa28b4)==0xb22d8 and call(m,0xa28e0)==0xb22d8 and call(m,0xa28f0)==0x1a768
assert word(0xa28f8)==0x7100133f and word(0xa2914)==0x6b1a033f
assert call(f,0xd4b5c)==0xd4760 and call(f,0xd47e4)==0x130100 and call(f,0xd4864)==0x12fe30
assert binding(f,0x130100)=='_$sSh8containsySbxF' and binding(f,0x12fe30)=='_$sSa6appendyyxnF'
assert f.u32(f.file_offset(0xd47ec))==0x370003e0 and f.u32(f.file_offset(0xd57d8))==0xf9400293
ranges=[]
for im,a,b in [(m,0x9de98,0x9e1d0),(m,0xa285c,0xa2940),(m,0x1a768,0x1a7ec),(f,0xd4760,0xd4890),(f,0xd4968,0xd4be0),(f,0xd57c4,0xd5858)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(im.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=im.data[im.file_offset(a):im.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':im.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(im.path.name+'-'+hex(a)+'.s')).write_text(text)
out={'images':[{'name':im.path.name,'sha256':sha(im.data),'uuid':im.uuid} for im in [m,f]],'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_getter_invoked':False,'semantics':'direct override list; section-order flatten preserving duplicates; overrides+grid stable full-value canonical-String dedup; no recursive child inclusion','effect_application_mapping_proven':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
