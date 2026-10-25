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
assert fields(0xd6e3c)==['id','displayName','renderEffects','interfaceOrientationOverride']
assert fields(0xd6fe0)==['id','displayName','renderEffects','interfaceOrientationOverride','renderEffect']
assert [project(0xa170c,0xa17bc,i) for i in range(5)]==fields(0xd6fe0)
assert fields(0xd702c)==fields(0xd7094)==['id']
assert fields(0xd7048)==fields(0xd6e7c)==['rawValue']
assert project(0xa4f80,0xa4f8c,0)=='id'
assert fields(0xd53fc)==fields(0xd5790)==['contentOverride']
assert project(0x6876c,0x68790,0)=='contentOverride'
assert [project(0x8f898,0x8f930,i) for i in range(4)]==fields(0xd63f4)==['portrait','portraitUpsideDown','landscapeLeft','landscapeRight']
assert word(0x8f878)==0x52800088 and word(0x8f87c)==0xf100129f and word(0x8f880)==0x9a883288
# First optional modern array, malformed present propagates, only nil retries.
assert word(0xa1a30)==0x52800048 and call(m,0xa1a50)==0x546c0
assert call(m,0xa1a68)==0xb1948 and word(0xa1a70)==0xb4000135
assert word(0xa1aa0)==0xb40002d8 and word(0xa1afc)==0x52800088
assert call(m,0xa1b04)==0x54730 and call(m,0xa1b20)==0xb190c
assert word(0xa1b28)==0xb5fffa75
# ID and display name required, then optional orientation.
assert word(0xa1aa8)==0x3900a3ff and call(m,0xa1aac)==0xa35cc and call(m,0xa1ac8)==0xb190c
assert word(0xa1b80)==0x52800028 and call(m,0xa1ba4)==0xb190c
assert binding(m,0xe4478,8)=='_$sSSN'
assert word(0xa1be8)==0x52800068 and call(m,0xa1bf0)==0x5936c and call(m,0xa1c0c)==0xb1948
# Legacy output is first effect, or literal Missing for an empty modern array.
assert word(0xa183c)==0xf9400aa8 and word(0xa1840)==0xb40000a8 and word(0xa1844)==0xa94252b9
assert word(0xa1854)==0xd2fce014
lo=0
for a in range(0xa1858,0xa1868,4):
 v=word(a);assert v&31==25 and v&0x7f800000 in [0x52800000,0x72800000]
 lo|=((v>>5)&65535)<<(((v>>21)&3)*16)
assert lo.to_bytes(8,'little')[:7]==b'Missing'
assert call(m,0xa18e8)==0xa35cc and call(m,0xa18f0)==0x546c0 and call(m,0xa18f8)==0x5936c and call(m,0xa1900)==0x54730
assert call(m,0xa1988)==0xb1ba0
# Effect dictionary requires opaque String-wrapper id. Exact symbols, no ABI call.
sym,ind,libs=tables(m);symbols={}
for j in range(sym[1]):
 n,k,section,d,v=m.unpack('<IBBHQ',sym[0]+16*j)
 if k&0xe==0xe and section:
  a=sym[2]+n;symbols[m.data[a:m.data.index(0,a)].decode()]=v
assert symbols['_$s21PreviewsMessagingHost12RenderEffectV2IDV8rawValueAESS_tcfC']==symbols['_$s21PreviewsMessagingHost14PreviewVariantV2IDV8rawValueAESS_tcfC']==0x36b38
assert call(m,0x36b38)==0x36358 and word(0x36358)==0xa9000500
assert call(m,0xa50a4)==0xa5030 and call(m,0xa50c0)==0xb190c
assert call(m,0xa4fb0)==0xa5030 and call(m,0xa4fdc)==0xb1978
# Selected override reply: absent optional String is accepted, present invalid errors.
assert call(m,0x68828)==0x24104 and call(m,0x68844)==0xb1948 and word(0x68870)==0xb5000076
assert call(m,0x687b4)==0x24104 and call(m,0x687e0)==0xb1978
regions=[(0xa170c,0xa17bc),(0xa17fc,0xa19ec),(0xa19ec,0xa1c9c),(0xa4f80,0xa4ff0),(0xa5070,0xa5110),(0x36b38,0x36b3c),(0x36358,0x36360),(0x8f824,0x8f930),(0x6876c,0x68894)]
ranges=[]
for a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(hex(a)+'.s')).write_text(text)
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_decoder_invoked':False,'effects_applied':False,'missing_modern_array_uses_required_legacy_effect':True,'malformed_modern_array_propagates':True,'empty_array_legacy_output_id':'Missing','override_result_absent_is_valid':True,'group_configuration_decoding_implemented':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
