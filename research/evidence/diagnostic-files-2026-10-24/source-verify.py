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
imports={hex(a):binding(a) for a in [0x12f2e4,0x12f2f0,0x12faa0,0x1305f8,0x131120,0x13112c]}
assert imports=={'0x12f2e4':'_$s10Foundation3URLV22appendingPathComponent_11isDirectoryACSS_SbtF','0x12f2f0':'_$s10Foundation3URLV22appendingPathComponentyACSSF','0x12faa0':'_$sSS10FoundationE8EncodingV4utf8ACvgZ','0x1305f8':'_$sSy10FoundationE5write2to10atomically8encodingyAA3URLV_SbSSAAE8EncodingVtKF','0x131120':'_os_unfair_lock_lock','0x13112c':'_os_unfair_lock_unlock'}
assert call(0xe29c4)==0x131120 and call(0xe29e8)==0xe2a0c and call(0xe2a08)==0x13112c
# Action values contain name, optional folder and contents; array grows by one.
assert word(0xe2aac)==0xa9016c1c and word(0xe2ab0)==0xa902641a and word(0xe2abc)==0xa9035809
assert word(0xe2a74)==0x910006f3 and word(0xe2ac4)==0xf9000b13
assert word(0xe0700)==0xf9400f61 and word(0xe0704)&0xff00001f==0xb4000001;conditional(0xe0704,0xe0788)
assert word(0xe0714)==0x52800022 and call(0xe0718)==0x12f2e4
assert word(0xe0754)==0x52800023 and word(0xe0758)==0xd2800004 and call(0xe075c)==0x131880
conditional(0xe0778,0xe07a0)
# Directory failure converts/releases the error, clears saved error and falls
# through to filename/write. It does not return or propagate this failure.
assert call(0xe07b0)==0x12f284 and call(0xe07cc)==0x131294
assert word(0xe07d0)==0xf81783bf
assert binding(0x12f284)=='_$s10Foundation22_convertNSErrorToErrorys0E0_pSo0C0CSgF'
assert binding(0x131294)=='_swift_errorRelease'
assert call(0xe0800)==0x12f2f0 and call(0xe0808)==0x12faa0
assert word(0xe0824)==0x52800021 and call(0xe0830)==0x1305f8
# Wrapper main then cause, identical retained collector argument, default noop.
assert word(0x5f748)==0xaa1403e0 and word(0x5f770)==0x9100a260
assert word(0x5f758)==word(0x5f780)==0xf94026e8
assert word(0x5f75c)==word(0x5f784)==0xaa1503e0
assert word(0x1e5c)==0xd65f03c0
nm=subprocess.run(['xcrun','nm','-n',str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode()
assert any(line.startswith('0000000000001e5c ') and 'RemoteHumanReadableError' in line and 'collectDiagnostics' in line for line in nm.splitlines())
assert any(line.startswith('000000000017f4e0 ') and 'WriteFileAction' in line and 'WP' in line for line in nm.splitlines())
assert any(line.startswith('0000000000131880 ') and '_objc_msgSend$createDirectoryAtURL:withIntermediateDirectories:attributes:error:' in line for line in nm.splitlines())
ranges=[]
for a,b in [(0xe2980,0xe2b38),(0xe0638,0xe08ac),(0x5f728,0x5f7a8),(0x1e5c,0x1e60)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'imports':imports,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'file_entry_fields':['name','optional_folder','contents'],'deferred_ordered_append':True,'write_utf8_atomically':True,'present_folder_creates_intermediate_directories':True,'wrapper_collect_order':['main','cause'],'canonical_remote_leaf_collect':'no-op','directory_creation_error_discarded_before_write':True,'private_collector_invoked':False}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
