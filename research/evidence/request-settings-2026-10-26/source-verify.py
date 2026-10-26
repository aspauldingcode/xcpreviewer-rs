from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest()
m=MachO(Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline'))
assert sha(m.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def binding(a):
 s,ind,libs=tables(m);sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()

def fields(a):
 _,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
assert fields(0x559710)[6:8]==['discoveredItemSettings','defaultPreviewSettings']
assert fields(0x55be78)==['isEnabled','boxedCanvasControlStates'] and fields(0x55bec8)==['states']
assert fields(0x5596e8)==['preview','registry']
# Both state fields have the exact same Array<HashableBox<PlistValueBox>> typeref.
assert m.relative(0x55be78+16+12+4)==m.relative(0x55bec8+16+4)==0x54f8ea
assert 0x54c269+m.unpack('<i',m.file_offset(0x54c269))[0]==0x5ac3d8
assert m.unpack('<Q',m.file_offset(0x5ac3d8))[0]==0x10000000568400
assert m.string(m.relative(0x568400+8))=='PreviewSettings' and m.relative(0x568400+16)==0x55be78
assert call(0x6f430)==0x17d8f4 and word(0x6f43c)==0x52800002 # PreviewInstance.id, enum preview tag0
assert call(0x6f448)==0x2b4ab4 and word(0x6f450)==0xb9802808 # settings field6 dictionary
assert word(0x6f46c)==0xb40003a8 and call(0x6f47c)==0xe2924 and word(0x6f480)==0x360002c1
assert word(0x6f488)==0x8b001108 and word(0x6f48c)==0x39400113 and word(0x6f494)==0xf9400518
assert word(0x6f4c0)==0x370002d3 and word(0x6f4d4)==0x14000568 # enabled branch vs empty return
assert word(0x6f4e0)==0xb9802f08 and word(0x6f4f0)==0x39400113 and word(0x6f4f8)==0xf9400518
assert word(0x6f514)==0x3607fd93 # default row disabled returns empty
assert word(0x6f51c)==0xf8100118 # selected control-state array retained for all request builders
assert word(0x6fa94)==0xf8500135 and word(0x6faa4)==0xa900d534
assert word(0x6fd44)==0xf8500134 and word(0x6fd48)==0xf9000914
assert word(0x708cc)==0xf8500139 and word(0x708d0)==0xa900e51b
assert word(0x460730)==0x3900011f and word(0x460738)==0xf9472d29 and word(0x46073c)==0xf9000509
nm=subprocess.run(['xcrun','nm','-nm',str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
symbols={line.split()[-1]:int(line.split()[0],16) for line in nm.splitlines() if re.match(r'^[0-9a-f]{16} ',line)}
assert symbols['_$s16PreviewsPipeline15PreviewSettingsVACycfC']==0x460730
assert symbols['_$s16PreviewsPipeline15PreviewInstanceV2idAC2IDVvg']==0x17d8f4
ranges=[]
for a,b,name in [(0x6f428,0x6f520,'settings-admission.s'),(0x460730,0x460744,'default-settings.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_previewRequests_invoked':False,'scope':'stored row/default row enabled gate and unchanged ordered state array propagation; structured native key lookup and box semantics remain caller-owned'}
(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
