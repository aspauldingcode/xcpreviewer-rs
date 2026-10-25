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

p=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline');assert sha(p.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
def pw(a):return p.u32(p.file_offset(a))
def imported(site,target,name):assert call(p,site)==target and binding(p,target)==name
a=0x5593e0;kind,size,n=p.unpack('<HHI',p.file_offset(a+8));assert size==12;assert [p.string(p.relative(a+16+i*size+8)) for i in range(n)]==['contentCategory','requestedOverrides']
imported(0x2a3fc4,0x51dce4,'_$s21PreviewsMessagingHost15ContentCategoryVMa')
imported(0x2a3ff8,0x51f8bc,'_$sSQ2eeoiySbx_xtFZTj')
assert binding(p,0x5afe88,8)=='_$s21PreviewsMessagingHost15ContentCategoryVSQAAMc'
assert binding(p,0x5afeb0,8)=='_$s21PreviewsMessagingHost15ContentOverrideVSQAAMc'
assert binding(p,0x5afe80,8)=='_$s21PreviewsMessagingHost15ContentCategoryVSHAAMc' and binding(p,0x5afea8,8)=='_$s21PreviewsMessagingHost15ContentOverrideVSHAAMc'
assert pw(0x2a3ffc)==0x36000100 and pw(0x2a4000)==0xb98016a8 and call(p,0x2a4018)==0x40da0 and call(p,0x40db8)==0x41194
assert pw(0x41228)==0x540005a1 and pw(0x412c8)==0x3600011b and pw(0x412cc)==0x8b13035a and pw(0x412d0)==0x8b130339
imported(0x41298,0x51f8bc,'_$sSQ2eeoiySbx_xtFZTj')
imported(0x2a3b44,0x51f82c,'_$sSH4hash4intoys6HasherVz_tFTj')
imported(0x2a3b60,0x520954,'_$ss6HasherV8_combineyySuF')
assert pw(0x2a3b58)==0xf9400ae0 # hashes array count before ordered entries
imported(0x2a3bc4,0x51f82c,'_$sSH4hash4intoys6HasherVz_tFTj')
assert pw(0x2a3bd8)==0x8b1802f7 and pw(0x2a3be0)==0x54fffd61
ranges=[]
for a,b,name in [(0x2a3ab8,0x2a3c04,'key-hash.s'),(0x2a3fa4,0x2a4030,'key-equality.s'),(0x40da0,0x40dbc,'array-equality-thunk.s'),(0x41194,0x4130c,'array-equality.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
# Named scalar witness aliases resolve through two shared thunks to Swift String
# comparison. Generic conformance descriptors have no static witness-table pattern;
# do not dereference that nil field or guess private runtime ABI.
nm=subprocess.run(['xcrun','nm','-nm',str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
for name in ['_$s21PreviewsMessagingHost15ContentCategoryVSQAASQ2eeoiySbx_xtFZTW','_$s21PreviewsMessagingHost15ContentOverrideVSQAASQ2eeoiySbx_xtFZTW']:
 rows=[line.split() for line in nm.splitlines() if line.split() and line.split()[-1]==name];assert len(rows)==1 and int(rows[0][0],16)==0x36b24
assert call(m,0x36b24)==0x36388 and call(m,0x36388)==0x366b0 and call(m,0x366d4)==0xb22d8
assert binding(m,0xb22d8)=='_$ss27_stringCompareWithSmolCheck__9expectingSbs11_StringGutsV_ADs01_G16ComparisonResultOtF'
assert call(p,0x6f610)==0x2b7988
for image,a,b,name in [(m,0x36b24,0x36b28,'wrapper-thunk.s'),(m,0x36388,0x3638c,'wrapper-shared-thunk.s'),(m,0x366b0,0x366e0,'wrapper-equality.s'),(p,0x6f610,0x6f614,'effective-call.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':'PreviewsMessagingHost' if image is m else 'PreviewsPipeline','start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(p.data),'uuid':p.uuid,'messaging_host_sha256':sha(m.data),'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'semantics':'content category equality then ordered positionwise override array equality; hash combines category,count,each ordered override; canonical Unicode wrapper identity inherited','native_cache_method_invoked':False,'native_hash_bits_parity':False,'native_memoization_coalescing_invalidation_parity':False,'preview_requests_constructor_located':'0x6ee3c..0x70b58','preview_requests_constructor_implemented':False}
q=w/'source-findings.json'
if q.exists():assert out==json.loads(q.read_text())
else:q.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
