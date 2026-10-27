from pathlib import Path
import sys,json,hashlib,re,subprocess
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');images={n:MachO(base/(n+'.framework')/'Versions/A'/n) for n in ['PreviewsMessagingHost','PreviewsPlatforms','PreviewsFoundationHost']};sha=lambda b:hashlib.sha256(b).hexdigest()
pins={'PreviewsMessagingHost':'0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c','PreviewsPlatforms':'e155b76d75ef6c37fa6685c8433e8e3cd7ca06f89fd598b5571cf52349d31cbd','PreviewsFoundationHost':'1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'}
for n,h in pins.items():assert sha(images[n].data)==h
m=images['PreviewsMessagingHost'];p=images['PreviewsPlatforms'];fd=m.relative(0xd1884+16);assert m.u32(m.file_offset(0xd1884+24))==4;assert m.u32(m.file_offset(fd+12))==1;assert m.string(m.relative(fd+24))=='messageRelay'
assert [m.u32(m.file_offset(a)) for a in [0x7519c,0x751ac]]==[0xa9400a88,0xa9401288]
assert m.u32(m.file_offset(0x74cfc))==0x528001c0 and m.u32(m.file_offset(0x74d00))==0x52800081
assert p.u32(p.file_offset(0x480dc))==0x30000 and p.u32(p.file_offset(0x480e0))==2
assert p.relative(0x480e8)==0x13448 and p.relative(0x480f0)==0x13514
s,ind,libs=tables(m)
def binding(a):
 sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()
assert binding(0xb2710)=='_swift_getWitnessTable'
assert binding(0xb1558)=='_$s10Foundation4DataV36_unconditionallyBridgeFromObjectiveCyACSo6NSDataCSgFZ'
assert binding(0xb1930)=='_$s22PreviewsFoundationHost12PropertyListV22serializableDictionaryACSDySSypG_tcfC'
ranges=[]
for image,a,b,label in [(m,0x74ca0,0x751bc,'receiver'),(m,0x75670,0x7567c,'metadata'),(m,0x75898,0x758a0,'receiver-destroy'),(m,0x6e998,0x6ebb8,'lazy-getter'),(m,0x3dbd8,0x3dd54,'unit-reply'),(p,0x14074,0x140ac,'role-metadata')]:
 t=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/(label+'.raw.s')).write_text(t);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',t,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'source_images':{n:{'sha256':sha(i.data),'uuid':i.uuid} for n,i in images.items()},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'receiver_field':'messageRelay','field_offset_vector_word':4,'availability_data_gate':[14,4,0],'scope':'Actual native Receiver<DaemonClientRole> protocol witnesses extract the messageRelay pair and use availability-selected UV data or legacy dictionary access. Current native controls qualify data path, preserved lazy bytes, optional native TransportReply copying/Unit send/drop observation. Legacy receiver branch is source-only; native connection construction/routing and finality/settlement remain unqualified. Original closure field initialization is layout-qualified; no native memberwise initializer is asserted.'};(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(out['source_bytes_verified'])
