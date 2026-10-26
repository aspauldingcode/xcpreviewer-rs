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

p=f
def pw(a):return p.u32(p.file_offset(a))
def imported(site,target,name):assert call(p,site)==target and binding(p,target)==name
# Exact symbol aliases disambiguate folded default-value stubs.
nm=subprocess.run(['xcrun','nm','-nm',str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
symbols={line.split()[-1]:int(line.split()[0],16) for line in nm.splitlines() if re.match(r'^[0-9a-f]{16} ',line)}
assert symbols['_$s22PreviewsFoundationHost18AsyncThrowingCacheC10invalidate3key13cancelingTaskyx_SbtFfA0_']==0x4788
assert symbols['_$s22PreviewsFoundationHost18AsyncThrowingCacheC14clearOnFailureACyxq_GSb_tcfcfA_']==0x4884
assert pw(0x4788)==0x52800020 and pw(0x4884)==0x52800000
imported(0xb3860,0x12f89c,'_$sSDyq_Sgxcig')
assert pw(0xb3874)==0xb4000218 # existing task skips factory+storage
assert call(p,0xb3948)==0xb468
imported(0xb39c0,0x12f8a8,'_$sSDyq_Sgxcis')
imported(0xb3a28,0x12ffbc,'_$sScT5valuexvg')
assert pw(0xb3be4)==0x3941c288 and pw(0xb3bec)==0x540002c1
assert pw(0xb3c0c)==0xf8068eff # nil optional assigned to dictionary at creator error
imported(0xb3c38,0x12f8a8,'_$sSDyq_Sgxcis')
# No dictionary lookup/task comparison in creator failure cleanup or reused failure.
assert 0x12f89c not in [call(p,a) for a in range(0xb3bc4,0xb3c88,4) if pw(a)>>26==37]
assert 0x12f8a8 not in [call(p,a) for a in range(0xb3b74,0xb3bc4,4) if pw(a)>>26==37]
assert pw(0xb3d44)==0x36000521 and pw(0xb3dc4)==0xb4000139
imported(0xb3ddc,0x12ffc8,'_$sScT6cancelyyF')
assert pw(0xb3dfc)==0xf81903bf
imported(0xb3e68,0x12f8a8,'_$sSDyq_Sgxcis')
a=0x159eb8;kind,size,n=p.unpack('<HHI',p.file_offset(a+8));assert size==12;assert [p.string(p.relative(a+16+i*size+8)) for i in range(n)]==['$defaultActor','clearOnFailure','storage']
ranges=[]
for a,b,name in [(0x4788,0x4790,'default-invalidate.s'),(0x4884,0x488c,'default-clear.s'),(0xb3634,0xb3e94,'cache.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
pipeline=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline');assert sha(pipeline.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
assert pipeline.relative(0x533268)==0x54bcaa
assert binding(pipeline,0x51eb6c)=='_$s22PreviewsFoundationHost18AsyncThrowingCacheC14clearOnFailureACyxq_GSb_tcfC'
for a in [0x2a407c,0x2a40a0,0x2a40c4]:assert pipeline.u32(pipeline.file_offset(a))==0x52800020
for a in [0x2a4080,0x2a40a4,0x2a40c8]:assert call(pipeline,a)==0x51eb6c
# The middle instantiation cache is ContentOverrideKey -> Optional<ContentOverride>.
pnm=subprocess.run(['xcrun','nm','-nm',str(pipeline.path)],capture_output=True,text=True,check=True,timeout=20).stdout
assert any(line.startswith('0000000000533268 ') and 'ContentOverrideKey' in line for line in pnm.splitlines())
a,b=0x2a4030,0x2a40f4
text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(pipeline.path)],capture_output=True,text=True,check=True,timeout=20).stdout
words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=pipeline.data[pipeline.file_offset(a):pipeline.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/'capabilities-cache-init.s').write_text(text);ranges.append({'image':'PreviewsPipeline','start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(p.data),'uuid':p.uuid,'pipeline_sha256':sha(pipeline.data),'destination_clear_on_failure':True,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'semantics':'actor stores task handles; hit reuses; default clearOnFailure false; creator-only failure may remove current key without identity guard; default invalidate cancels then removes; task scheduling/awaiting/result/settlement not modeled','native_actor_invoked':False,'native_executor_timing_parity':False,'global_resource_settlement_proven':False,'swift_module_entries':list(map(str,p.path.parent.glob('Modules/*')))}
q=w/'source-findings.json'
if q.exists():assert out==json.loads(q.read_text())
else:q.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
