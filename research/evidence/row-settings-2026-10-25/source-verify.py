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

p=MachO('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode');assert sha(p.data)=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'
def pw(a):return p.u32(p.file_offset(a))
a=0x30bc70;kind,size,count=p.unpack('<HHI',p.file_offset(a+8));assert size==12 and [p.string(p.relative(a+16+i*size+8)) for i in range(count)]==['variantGroup','_overrides','_sortedChildConfigurations']
assert call(p,0x1eab2c)==0x2aa0b0 and binding(p,0x2aa0b0)=='_$s7SwiftUI7BindingV12wrappedValuexvg'
assert call(p,0x1eaaec)==0x2a75b4 and binding(p,0x2a75b4)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV2idAC2IDVvg'
assert call(p,0x1eab50)==0x227f90 and pw(0x1eab54)==0x36000501
assert pw(0x1eac68)==0x54000301 and pw(0x1eacf4)==0x14000018
assert call(p,0x1eac74)==0x2a7578 and binding(p,0x2a7578)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV22overridesConfigurationAA0d9OverridesH0VSgvg'
assert pw(0x1eaca0)==0x540002c1 and binding(p,0x3336b0,8)=='__swiftEmptySetSingleton'
assert call(p,0x1eacfc)==0x2a7884 and binding(p,0x2a7884)=='_$s21PreviewsMessagingHost29PreviewOverridesConfigurationV16defaultSelectionShyAA0D7VariantV2IDVGvg'
assert pw(0x1ead18)==0x52800000 and call(p,0x1ead20)==0x2a5cb8
assert binding(p,0x2a5cb8)=='_$s16PreviewsPipeline14EditorSettingsV012VariantGroupD0V9isEnabled9selectionAESb_Shy0A13MessagingHost07PreviewE0V2IDVGtcfC'
calls=[call(p,a) for a in range(0x1ea9ec,0x1ead74,4) if pw(a)>>26==37]
assert 0x2aa0bc not in calls # Binding.wrappedValue setter import, separately observed in setter closure.
a,b=0x1ea9ec,0x1ead74
text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/'complete-row-getter.s').write_text(text)
out={'image_sha256':sha(p.data),'uuid':p.uuid,'range':{'start':hex(a),'bytes':b-a,'sha256':sha(raw)},'selected_source_bytes_verified':b-a,'native_private_binding_getter_invoked':False,'semantics':'canonical group ID lookup; existing entire state wins; absent state returns disabled plus config defaultSelection or empty set; read does not install fallback','setter_semantics_implemented':False,'native_binding_or_persistence_parity':False,'default_representation_policy':'inherits deterministic portable default-selection traversal, distinct from randomized native sibling representative choice'}
q=w/'source-findings.json'
if q.exists():assert out==json.loads(q.read_text())
else:q.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
