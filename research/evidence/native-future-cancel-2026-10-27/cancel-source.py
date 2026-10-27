from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
fd=m.relative(0x151740+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert kind==0 and size==12 and n==4
fields=[m.string(m.relative(fd+16+i*12+8)) for i in range(n)];assert fields==['file','line','column','function']
def call(a):
 v=m.u32(m.file_offset(a));assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
assert call(0x115e40)==0x1187c8 and call(0x341f8)==0x34224
assert m.u32(m.file_offset(0x118bbc))==0xf9405908 and m.u32(m.file_offset(0x1187ec))==0xf9406108
assert m.u32(m.file_offset(0x341ec))==0x52800042
ranges=[]
for a,b in [(0x115e1c,0x115e44),(0x1187c8,0x118804),(0x118bb8,0x118bc4),(0x34178,0x34224)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/('cancel-'+hex(a)+'.raw.s')).write_text(text);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'callsite_fields':fields,'public_cancel_dispatch_slot':'0xb0','callsite_cancel_dispatch_slot':'0xc0','scope':'Exported Future.cancel thunk dispatches via b0; its wrapper assembles Callsite and dispatches via c0. The owned runtime invokes the actual c0 override only after its image/offset guard. PromiseFuture override copies Callsite into canceled tag2 and calls the qualified transition path. Runtime reflects only the owned returned snapshot value. Public wrapper itself is not invoked; base abstract implementation is not called. No transport cancellation, observer/queue/concurrency or resource settlement claimed.'};(w/'cancel-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(out['source_bytes_verified'])
