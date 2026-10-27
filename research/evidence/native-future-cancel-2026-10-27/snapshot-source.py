from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def cases(descriptor):
 fd=m.relative(descriptor+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert kind==2 and size==12
 return [m.string(m.relative(fd+16+i*12+8)) for i in range(n)]
assert cases(0x15476c)==['finished','running'];assert cases(0x1559e8)==['succeeded','failed','canceled']
assert [m.u32(m.file_offset(a)) for a in range(0x118b7c,0x118b88,4)]==[0xf9400289,0xf9404120,0xd61f0000]
ranges=[]
for a,b in [(0x115868,0x115964),(0x118b7c,0x118b88)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/('snapshot-'+hex(a)+'.s')).write_text(text);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
assert sum(x['bytes'] for x in ranges)==264
out={'image_sha256':sha(m.data),'uuid':m.uuid,'future_state_cases':cases(0x15476c),'future_termination_cases':cases(0x1559e8),'snapshot_dispatch_metadata_slot':'0x80','ranges':ranges,'source_bytes_verified':264,'scope':'Actual exported virtual snapshot getter dispatches through class metadata slot0x80; owned runtime verifies resolved native getter offset0x115868. Getter returns FutureState via indirect result and native synchronous peek/state path. Runtime reflection applies only to the returned owned value copy, not mutable lock storage. No cancellation or final provider/OS resource settlement claimed.'};(w/'snapshot-findings.json').write_text(json.dumps(out,indent=2)+'\n');print('Verified264 snapshot source bytes and enum descriptors')
