from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def call(a):
 v=m.u32(m.file_offset(a));assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
assert call(0x34238)==0x34544 and call(0x3443c)==0x34224 and call(0x34cf0)==0x343a4 and call(0x34db8)==0x343a4
assert call(0x34868)==0x348c4 and call(0x3427c)==0x71290
assert m.u32(m.file_offset(0x34774))==0x54000261
ranges=[]
for a,b in [(0x34224,0x34298),(0x343a4,0x34468),(0x34544,0x348c4),(0x34b48,0x34de4)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/('transition-'+hex(a)+'.raw.s')).write_text(text);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'scope':'Promise succeed/fail reach complete, transition, tryTransition and the locked FutureState closure. Running branch replaces state; already completed old/new branch constructs TransitionError without replacing stored state, then transition handles its diagnostic path. Runtime independently measures retained first success/failure across repeated encoded callbacks. No cancellation, observer cardinality, queue/concurrency equivalence or resource settlement claimed.'};(w/'transition-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(out['source_bytes_verified'])
