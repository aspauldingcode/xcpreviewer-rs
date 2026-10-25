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
assert fields(0xd5390)==fields(0xd5724)==['contentCategory','contentOverride']
assert fields(0xd53d4)==fields(0xd5768)==['contentCategory','requestedOverrides']
assert fields(0xd41a4)==fields(0xd41dc)==['rawValue']
assert [project(0x67bbc,0x67c10,i) for i in range(2)]==fields(0xd5724)
assert [project(0x68374,0x683c0,i) for i in range(2)]==fields(0xd5768)
def definitions():
 sym,ind,libs=tables(m);out={}
 for i in range(sym[1]):
  n,k,section,d,v=m.unpack('<IBBHQ',sym[0]+16*i)
  if k&0xe==0xe and section:
   a=sym[2]+n;out[m.data[a:m.data.index(0,a)].decode()]=v
 return out
symbols=definitions()
for name in ['ContentCategory','ContentOverride']:
 assert symbols['_$s21PreviewsMessagingHost15'+name+'V8rawValueACSS_tcfC']==0x36b38
 assert symbols['_$s21PreviewsMessagingHost15'+name+'VSYAASY8rawValuexSg03RawG0Qz_tcfCTW']==0x36b14
assert call(m,0x36b38)==0x36358 and call(m,0x36b14)==0x36360
assert word(0x36358)==0xa9000500 and word(0x36360)==0xa9402809 and word(0x36364)==0xa9002909
assert call(m,0x363d0)==call(m,0x36724)==0xb1c30
assert call(m,0x36420)==call(m,0x36774)==0xb1c3c
assert binding(m,0xe5300,8)=='_$sSS0A10Foundation16PropertyListTypeAAWP'
# Required category precedes optional override, and errors propagate.
assert word(0x67d6c)==0x390063ff and call(m,0x67d70)==0x240c4
assert call(m,0x67d8c)==0xb190c and word(0x67dc8)==0x52800028
assert call(m,0x67dd0)==0x24104 and call(m,0x67dec)==0xb1948
assert word(0x67e10)==0xb40001b3
assert call(m,0x67c88)==0x240c4 and call(m,0x67c90)==0x24104 and call(m,0x67ce4)==0xb1bc4
# Override request has required category followed by required array of wrappers.
assert call(m,0x6852c)==0x240c4 and call(m,0x68548)==call(m,0x685dc)==0xb190c
assert word(0x68584)==0x52800028
array_name='_$sSay21PreviewsMessagingHost15ContentOverrideVG'
assert symbols[array_name+'MD']==0xf8938
assert symbols[array_name+'SayxG0a10FoundationC025PropertyListRepresentableA2fGRzlWL']==0xf8940
assert call(m,0x685c4)==call(m,0x6847c)==0x11e1c
assert call(m,0x6845c)==0x240c4 and call(m,0x684b0)==0xb1bc4
# Request kinds (not similarly named reply payloads).
for kind,content,decoder,getter,witness,error_site,tag_site in [(12,10,0x5fe58,0x5ec60,0x5ee9c,0x5fea0,0x5fed0),(13,11,0x6010c,0x5e9a0,0x5ee1c,0x60154,0x60184)]:
 expected=['variants','contentOverride'][kind-12]
 assert fields(0xd4ec0)[kind]==fields(0xd4f78)[content]==expected
 assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a+2*kind))[0]==decoder
 assert 0x5e96c+4*m.data[m.file_offset(0xba16d)+content]==getter
 assert call(m,decoder+0x20)==witness
 assert word(tag_site)==0x52800002+(content<<5)
assert call(m,0x5fe98)==call(m,0x6014c)==0xb1c24
assert word(0x5fea0)==0xb5002275 and word(0x60154)==0xb5000cd5
regions=[(0x67bbc,0x67e64),(0x68374,0x68650),(0x36358,0x3636c),(0x3638c,0x36438),(0x366e0,0x3678c),(0x36b14,0x36b1c),(0x36b38,0x36b3c),(0x5fe58,0x5fed8),(0x6010c,0x6018c),(0x5ec60,0x5eca4),(0x5e9a0,0x5e9f0)]
ranges=[]
for a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)}
 raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(hex(a)+'.s')).write_text(text)
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'native_private_decoder_invoked':False,'native_variant_discovery_or_override_performed':False,'variants_request':['contentCategory:required String wrapper','contentOverride:optional String wrapper'],'override_request':['contentCategory:required String wrapper','requestedOverrides:required array of String wrappers'],'category_and_override_are_open_strings':True}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
