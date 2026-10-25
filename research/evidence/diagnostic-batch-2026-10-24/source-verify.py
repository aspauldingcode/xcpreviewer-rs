from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def conditional(a,target):
 v=word(a);n=(v>>5)&0x7ffff;assert a+4*(n-(1<<19) if n&(1<<18) else n)==target
s,ind,libs=tables(m);sec=next(x for x in m.sections if x['flags']&255==8)
def binding(a):
 i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()
assert m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
imports={hex(a):binding(a) for a in [0x131120,0x13112c,0x131294,0x1312a0,0x1305f8,0x1305d4,0x12f974]}
assert imports['0x131120']=='_os_unfair_lock_lock' and imports['0x13112c']=='_os_unfair_lock_unlock'
assert imports['0x131294']=='_swift_errorRelease' and imports['0x1312a0']=='_swift_errorRetain'
assert 'write2to10atomically8encoding' in imports['0x1305f8'] and 'replacingOccurrences2of4with7options5range' in imports['0x1305d4'] and 'joined9separator' in imports['0x12f974']
assert call(0xdf39c)==0xe51a4 and call(0xdf3a4)==0xe58b4
conditional(0xdf3ac,0xdfa48)
# Snapshot actions/logs under lock; retained local copies, not state draining.
assert call(0xdf3cc)==0x131120 and word(0xdf3d4)==0xa9c1629c
assert call(0xdf3dc)==call(0xdf3e4)==0x1311e0 and call(0xdf3ec)==0x13112c
# Encounter-order loop and error append, reset and continue.
assert word(0xdf824)==0xf9400728 and word(0xdf838)==0xd63f0100
conditional(0xdf840,0xdf7e4)
assert call(0xdf848)==0x1312a0 and word(0xdf7d4)==0xf900111a
assert call(0xdf7dc)==0x131294 and word(0xdf7e0)==0xd280001a
assert word(0xdf7ec)==0x9100a2f7 and word(0xdf7f0)==0xf100077b
conditional(0xdf7f4,0xdf8b0)
assert call(0xdf884)==0xdf7cc and call(0xdf8a4)==0xdf858
# Report write error is released/cleared; optional ZIP has independent result.
assert call(0xdf9e0)==0x1305f8;conditional(0xdf9e8,0xdf9f8)
assert call(0xdf9f0)==0x131294 and word(0xdf9f4)==0xd280001a
assert word(0xdfa24)&0x7e000000==0x36000000 and call(0xdfa30)==0xe5ad4
assert word(0xdfa48)==0xaa1a03f5
# Fixed report filename and original native interpolation helper, no guessed ABI.
assert m.data[m.file_offset(0x1467c0):m.file_offset(0x1467c0)+23]==b'SerializationErrors.txt'
assert call(0xdf904)==0x12f974 and call(0xdf970)==0x1305d4
assert call(0xe5d28)==0x130940
ranges=[]
for a,b in [(0xdf2c8,0xdfb48),(0xe5cd4,0xe5d44)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'imports':imports,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'action_failures_continue_in_order':True,'source_action_queue_retained':True,'report_write_failure_discarded':True,'archive_setup_and_zip_failure_separate':True,'private_collector_invoked':False}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
