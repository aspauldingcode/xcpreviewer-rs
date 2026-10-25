from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest()
f=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost')
assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d';assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
def word(image,a):return image.u32(image.file_offset(a))
def call(image,a):
 v=word(image,a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def conditional(image,a,target,bits=19,shift=5):
 v=word(image,a);n=(v>>shift)&((1<<bits)-1);assert a+4*(n-(1<<bits) if n&(1<<(bits-1)) else n)==target

def binding(image,a):
 sym,ind,libs=tables(image);sec=next(s for s in image.sections if s['flags']&255==8);i=index(image,sec,a,12,ind);n,k,ss,d,v=image.unpack('<IBBHQ',sym[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=sym[2]+n;return {'symbol':image.data[o:image.data.index(0,o)].decode(),'library':libs[(d>>8)-1]}
imports={hex(a):binding(f,a) for a in [0x131270,0x131294]};assert imports['0x131270']['symbol']=='_swift_dynamicCast';assert imports['0x131294']['symbol']=='_swift_errorRelease'
human=binding(m,0xb22fc);assert human['symbol']=='_$ss5ErrorP22PreviewsFoundationHostE13humanReadableAC05HumanfA0_pvg'
# Key address and explicit length from the native string construction.
assert [word(f,a) for a in range(0x60f5c,0x60f68,4)]==[0xf0000708,0x9127c108,0xd1008115]
assert f.string(0x1439f0)=='UVHumanReadableError';assert word(f,0x60f74)==0xd2800280
assert f.string(f.relative(0x136a48))=='SDySSypG'
for a,t in [(0x60fb8,0x2710),(0x60fd0,0x131270),(0x60fec,0x5f154),(0x611b4,0x131294),(0x5d0ec,0x60eb4)]:assert call(f,a)==t
# Empty outer info, missing key/value, failed dictionary cast and unarchive error.
for a,t,bits in [(0x60f58,0x61134,19),(0x60f80,0x6112c,14),(0x60fa4,0x61144,19),(0x60fd4,0x6115c,14),(0x60ff0,0x61188,19)]:conditional(f,a,t,bits)
assert word(f,0x60ff0)&0xff00001f==0xb4000015
assert word(f,0x6115c)==0xf90012ff and word(f,0x61164)==0xad0002e0
# Caller only attempts humanReadable on the nil-payload / present-error branch.
conditional(m,0x3fce0,0x3fd88);conditional(m,0x3fd8c,0x3ffa0);assert call(m,0x3fe58)==0xb22fc
ranges=[]
for image,a,b in [(f,0x60eb4,0x611ec),(f,0x5cf68,0x5d138),(m,0x3fcb8,0x3fe5c)]:
 output=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',output,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'images':[{'image':i.path.name,'sha256':sha(i.data),'uuid':i.uuid} for i in [f,m]],'imports':imports,'human_readable_import':human,'archive_key':'UVHumanReadableError','archive_dictionary_mangling':'SDySSypG','unarchive_error_suppressed':True,'lazy_error_projection_after_payload_absence':True,'ranges':ranges,'selected_source_bytes_verified':sum(v['bytes'] for v in ranges),'private_swift_runtime_invoked':False,'full_remote_archive_schema_implemented':False,'target_settlement_proven':False}
artifact=Path(__file__).parent/'source-findings.json'
if artifact.exists():assert out==json.loads(artifact.read_text())
else:artifact.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
