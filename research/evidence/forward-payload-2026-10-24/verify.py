"""Bounded offline straight-line getter projection and forwarding-source checks."""
from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');pins={'PreviewsMessagingHost':'0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c','PreviewsPlatforms':'e155b76d75ef6c37fa6685c8433e8e3cd7ca06f89fd598b5571cf52349d31cbd'};images={n:MachO(base/(n+'.framework')/'Versions/A'/n) for n in pins}
for n,m in images.items():assert hashlib.sha256(m.data).hexdigest()==pins[n]
m=images['PreviewsMessagingHost'];p=images['PreviewsPlatforms']
def fields(a):
 kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
assert fields(0xd5310)==fields(0xd56a4)==['messageType','messagePayload','pid','contentDomain','previewInterfaceOrientation','sceneIdentifier']
assert fields(0xd6634)==['view','widget','complication'];assert fields(0xd63f4)==['portrait','portraitUpsideDown','landscapeLeft','landscapeRight']
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
keys=[project(0x66d70,0x66e4c,i) for i in range(6)];assert keys==['messageType','messagePayload','pid','previewContextType','previewInterfaceOrientation','sceneIdentifier']
domains=[project(0x95ec4,0x95f2c,i) for i in range(3)];assert domains==['application','widget','complication']
orientations=[project(0x8f898,0x8f930,i) for i in range(4)];assert orientations==fields(0xd63f4)
def binding(image,a):
 s,ind,libs=tables(image);sec=next(t for t in image.sections if t['flags']&255==8);i=index(image,sec,a,12,ind);n,k,ss,d,v=image.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;e=image.data.find(b'\0',o);return {'symbol':image.data[o:e].decode(),'library':libs[(d>>8)-1]}
bindings={'required':binding(m,0xb190c),'optional':binding(m,0xb1948),'incremental':binding(p,0x46028),'forward_init':binding(p,0x45ea8)}
assert '14unarchiveValue' in bindings['required']['symbol'];assert '22unarchiveOptionalValue' in bindings['optional']['symbol'];assert '18incrementalVariant' in bindings['incremental']['symbol'];assert 'ForwardPayloadV11messageType' in bindings['forward_init']['symbol']
def branch(image,a):
 i=image.u32(image.file_offset(a));assert i>>26 in [5,0x25];v=i&0x3ffffff;v=v-(1<<26) if v&(1<<25) else v;return a+4*v
for a,target in [(0x6724c,0xb190c),(0x672ac,0xb190c),(0x6732c,0xb190c),(0x67378,0xb1948),(0x673c4,0xb1948),(0x67410,0xb1948)]:assert branch(m,a)==target
assert m.u32(m.file_offset(0x67440))==0x7100111f;assert m.u32(m.file_offset(0x67444))==0x1a8803e8
assert p.u32(p.file_offset(0x3503c))==0x360000c8;assert branch(p,0x3504c)==0x46028;assert branch(p,0x35114)==0x45ea8;assert branch(p,0x3516c)==0x33134
regions={'PreviewsMessagingHost':[(0x66d70,0x66e4c),(0x67178,0x674e4),(0x95ec4,0x95f2c),(0x8f898,0x8f930)],'PreviewsPlatforms':[(0x35038,0x35180)]};bodies=[]
for name,rs in regions.items():
 image=images[name]
 for a,b in rs:
  text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert b''.join(words[x] for x in range(a,b,4))==raw;bodies.append({'target':name,'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'pins':pins,'uuids':{n:i.uuid for n,i in images.items()},'keys':keys,'domain_raw_values':domains,'orientation_raw_values':orientations,'required_keys':keys[:3],'optional_keys':keys[3:],'missing_orientation_fallback':'portrait','import_bindings':bindings,'selected_ranges':bodies,'selected_source_bytes_verified':sum(b['bytes'] for b in bodies),'source_only':True,'actual_transport_observed':False,'native_functions_invoked':False,'limits':'Getter projection covers13 valid tags in bounded instruction subset. No native coercion/null, serializer byte equality, reply or settlement parity.'},indent=2))
