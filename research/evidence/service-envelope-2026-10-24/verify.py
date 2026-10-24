"""Offline forward-only envelope verification; no native send or reply test."""
from pathlib import Path
import json,sys,hashlib,subprocess,re,plistlib
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');pins={'PreviewsMessagingHost':'0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c','PreviewsPlatforms':'e155b76d75ef6c37fa6685c8433e8e3cd7ca06f89fd598b5571cf52349d31cbd'};images={n:MachO(base/(n+'.framework')/'Versions/A'/n) for n in pins}
for n,m in images.items():assert hashlib.sha256(m.data).hexdigest()==pins[n]
m=images['PreviewsMessagingHost'];p=images['PreviewsPlatforms']
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
def fields(a):
 kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
assert fields(0xd4e98)==['identifier','content'];assert fields(0xd5434)==['messageType','payload'];assert fields(0xd5418)==['identifier']
types=fields(0xd4ec0);content=fields(0xd4f78);assert len(types)==14 and types[6]=='forward';assert len(content)==13 and content[4]=='forward'
keys=[project(0x5f308,0x5f34c,i) for i in range(2)];assert keys==['messageType','payload'];identifier=project(0x5f438,0x5f454,0);assert identifier=='__unique_service_message_identifier';assert project(0x60874,0x6088c,0)=='forward'
o=m.file_offset(0xba196);assert 0x60784+4*m.data[o+6]==0x60874
assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a+2*6))[0]==0x6018c
def binding(image,a):
 s,ind,libs=tables(image);sec=next(t for t in image.sections if t['flags']&255==8);i=index(image,sec,a,12,ind);n,k,ss,d,v=image.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;e=image.data.find(b'\0',o);return {'symbol':image.data[o:e].decode(),'library':libs[(d>>8)-1]}
bindings={hex(a):binding(m,a) for a in [0xb1900,0xb190c,0xb1948]};bindings.update({hex(a):binding(p,a) for a in [0x45f50,0x45f74,0x46850]})
assert '12archiveValue' in bindings['0xb1900']['symbol'];assert '14unarchiveValue' in bindings['0xb190c']['symbol'];assert '22unarchiveOptionalValue' in bindings['0xb1948']['symbol'];assert 'ServiceMessageVyA2C7ContentOcfC' in bindings['0x45f50']['symbol'];assert 'TransportReplyV4file' in bindings['0x45f74']['symbol'];assert 'FutureC9dsoHandle' in bindings['0x46850']['symbol']
def branch(image,a):
 i=image.u32(image.file_offset(a));assert i>>26 in [5,0x25];v=i&0x3ffffff;v=v-(1<<26) if v&(1<<25) else v;return a+4*v
for a,target in [(0x5f754,0xb190c),(0x5f7ac,0xb190c),(0x5fc3c,0xb1948),(0x5ed18,0xb1900),(0x60194,0x5ee08)]:assert branch(m,a)==target
assert branch(p,0x331bc)==0x46850;assert branch(p,0x33294)==0x45f74;assert branch(p,0x332ac)==0x327e0;assert branch(p,0x32980)==0x45f50
# Independent fixture schema and full nested64-byte data expectation.
f=r/'tools/re/rust/canvas-core/tests/fixtures/service-envelope/forward.bplist';forward=plistlib.loads((r/'tools/re/rust/canvas-core/tests/fixtures/forward-payload/full.bplist').read_bytes());forward[identifier]='owned/request/🪨';forward['messagePayload'][identifier]='nested-not-envelope';expected={'messageType':'forward','payload':forward};assert f.read_bytes()==plistlib.dumps(expected,fmt=plistlib.FMT_BINARY,sort_keys=True);assert forward['messagePayload']['padding']==bytes(range(64))
regions={'PreviewsMessagingHost':[(0x5f308,0x5f34c),(0x5f438,0x5f454),(0x60874,0x6088c),(0x5f684,0x5f840),(0x5fc0c,0x5fc44),(0x6018c,0x60210),(0x5ece4,0x5ed44)],'PreviewsPlatforms':[(0x33134,0x332e0),(0x327e0,0x32ca4)]};bodies=[]
for name,rs in regions.items():
 image=images[name]
 for a,b in rs:
  text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert b''.join(words[x] for x in range(a,b,4))==raw;bodies.append({'target':name,'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'pins':pins,'uuids':{n:i.uuid for n,i in images.items()},'outer_keys':keys,'payload_identifier_key':identifier,'forward_outer_kind':'forward','metadata_message_type_case':6,'metadata_content_case':4,'internal_ordinals_are_wire_values':False,'import_bindings':bindings,'selected_ranges':bodies,'selected_source_bytes_verified':sum(b['bytes'] for b in bodies),'fixture_bytes':f.stat().st_size,'source_only':True,'native_functions_invoked':False,'actual_transport_observed':False,'reply_matching':False,'identifier_generation_recovered':False},indent=2))
