from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
sha=lambda b:hashlib.sha256(b).hexdigest()
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
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
assert project(0x68998,0x689bc,0)=='isRunningInXTP'
assert project(0x60784,0x607a4,1)=='capabilities'
assert fields(0xd4ec0)[1]=='capabilities' and fields(0xd4f78)[0]=='capabilities'
assert fields(0xd5164)==['isRunningInXTP'] and fields(0xd57ac)==['isRunningInXTP']
assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a+2))[0]==0x5ff94
assert 0x5e96c+4*m.data[m.file_offset(0xba16d)]==0x5ead0
assert call(0x5ffd4)==0xb1c24 and call(0x5ffe0)==0xb25fc
assert word(0x5ffe4)==0xd2800017 and word(0x5ffe8)==0x52800054 and call(0x5ffec)==0x6039c
assert word(0x60398)==0x39438274 and word(0x603c0)==0x38366b14 and word(0x603cc)==0x52800002 and call(0x603d0)==0xb27dc
assert word(0x5ead4)==0x7100091f and word(0x5eadc)==0x54001341
assert call(0x5ed4c)==0x5f104 and call(0x5ed64)==0xb1c18
assert call(0x68aac)==0xb190c and word(0x68adc)==0x385ef3a8 and word(0x68ae0)==0x39000268
imports={hex(a):binding(m,a) for a in [0xb190c,0xb1c24,0xb25fc,0xb1c18,0xb1cb4]}
assert imports['0xb25fc']=='_swift_errorRelease'
assert imports['0xb1c24']=='_$s22PreviewsFoundationHost25PropertyListRepresentablePAAE08propertyE0xAA0dE0V_tKcfC'
assert call(0x63088)==0xb1cb4
assert word(0x698c8)==0x39404288 and word(0x698cc)==0x39000028 and word(0x698d0)==0xd65f03c0
bool_metadata=binding(m,0xe4560,8);assert bool_metadata=='_$sSbN'
def fcall(a):
 v=f.u32(f.file_offset(a));assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
assert fcall(0x98a68)==0x9c5f8 and fcall(0x9c79c)==0x9c93c and fcall(0x9c9d4)==0x131270
assert binding(f,0x131270)=='_swift_dynamicCast'
regions=[('Messaging',m,0x698c8,0x698d4),('Messaging',m,0x63078,0x630a0),('Messaging',m,0x68998,0x689bc),('Messaging',m,0x689fc,0x68afc),('Messaging',m,0x5ff94,0x5fff0),('Messaging',m,0x60394,0x603d8),('Messaging',m,0x5ead0,0x5eaf4),('Messaging',m,0x5ed44,0x5edcc),('Messaging',m,0x60784,0x607a4),('Foundation',f,0x98990,0x98b18),('Foundation',f,0x9c5f8,0x9c83c),('Foundation',f,0x9c93c,0x9cabc),('Foundation',f,0x9abb8,0x9abc4)]
ranges=[]
for name,image,a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
 # Source bytes/disassembly remain local, never copied to public bundle.
 (w/(name+'-'+hex(a)+'.s')).write_text(text)
out={'images':{'Messaging':{'sha256':sha(m.data),'uuid':m.uuid},'Foundation':{'sha256':sha(f.data),'uuid':f.uuid}},'wire_kind':'capabilities','kind_internal_ordinal':1,'content_internal_ordinal':0,'payload_key':'isRunningInXTP','required_bool_field':True,'default_runtime_detection_invoked':False,'outer_decode_error_suppressed_to_absent':True,'identifier_errors_suppressed':False,'imports':imports,'bool_metadata_import':bool_metadata,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_functions_invoked':False,'native_capability_delivery_observed':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
