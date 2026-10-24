"""Source-only verification of context construction, not a transport send."""
from pathlib import Path
import sys,json,subprocess,hashlib,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.chained import rebase
from reloop.stubbind import tables,index
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');pins={'PreviewsDeveloperTools':'d70f346fc8c8f7085f0a8b05fe160776b5464a3a6efc146259076fd12aa21cc2','PreviewsMessagingHost':'0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c','PreviewsPipeline':'c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'}
images={n:MachO(base/(n+'.framework')/'Versions/A'/n) for n in pins}
for n,m in images.items():assert hashlib.sha256(m.data).hexdigest()==pins[n]
def symbol(m,address,stride):
 s,ind,libs=tables(m);sec=next(t for t in m.sections if t['address']<=address<t['address']+t['size']);i=index(m,sec,address,stride,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;e=m.data.find(b'\0',o);return {'name':m.data[o:e].decode(),'library':libs[(d>>8)-1]}
d=images['PreviewsDeveloperTools'];p=images['PreviewsPipeline'];m=images['PreviewsMessagingHost']
bindings={hex(a):symbol(d,a,12) for a in [0x9975c,0x991c8,0x991d4]}
assert bindings['0x9975c']['name']=='_$s21PreviewsMessagingHost16AgentMessageTypeOMa'
assert 'PlatformPreviewUpdateContextV15defaultArchiver' in bindings['0x991c8']['name']
assert bindings['0x991d4']['name'].endswith('tcfcfA1_')
for a,word in [(0x24d2c,0xf90076c0),(0x24d30,0xf85f8008),(0x24d34,0xf9007ac8),(0x24e6c,0xf900c6c0),(0x2561c,0xa958a6c8),(0x25624,0xf9004be8),(0x25674,0xa94eaac9),(0x25678,0xa90627ea),(0x25810,0xf9404be8),(0x25814,0xb9802508),(0x25838,0xa9460be8),(0x2583c,0xf9403508),(0x25844,0xaa1703e0),(0x25848,0xd63f0100),(0x2585c,0xaa1403e8),(0x25878,0xaa1403e2),(0x2587c,0xaa1703e3)]:assert d.u32(d.file_offset(a))==word
for a,target in [(0x24d28,0x9975c),(0x24e68,0x20fa8),(0x25860,0x991d4),(0x25880,0x991c8)]:
 ins=d.u32(d.file_offset(a));assert ins>>26==0x25;v=ins&0x3ffffff;v=v-(1<<26) if v&(1<<25) else v;assert a+v*4==target
assert rebase(m,0xeea70)['target']==0xee9f8
witness=rebase(m,0xee9f8+0x68);assert witness['target']==0x3950
assert m.u32(m.file_offset(0x3950))==0x17fffe9a
assert [m.u32(m.file_offset(a)) for a in [0x33b8,0x33bc]]==[0x39000001,0xd65f03c0]
defaults={hex(a):symbol(p,a,8) for a in [0x5aff40,0x5aff48,0x5aff50]}
assert 'O6renderyA2CmFWC' in defaults['0x5aff40']['name'];assert 'O7displayyA2CmFWC' in defaults['0x5aff48']['name'];assert defaults['0x5aff50']['name'].endswith('AgentMessageTypeOMa')
# Default helper tail-dispatch is through metadata-minus-eight's enum slot0x68.
for a,word in [(0x235c,0xaa0003e2),(0x2360,0xf85f8008),(0x2364,0xf9403503),(0x2378,0xd61f0060),(0xc88bc,0xaa0303f3),(0xc88c0,0xaa0203f5),(0xc8988,0xaa1503e1),(0xc899c,0xaa1303e1)]:assert p.u32(p.file_offset(a))==word
assert [p.string(p.relative(0x5560ec+16+i*12+8)) for i in range(4)]==['defaultArchiver','overrideArchivers','legacyHostedPreviewMessage','legacyStaticPreviewMessage']
regions={'PreviewsDeveloperTools':[(0x24d24,0x24d38),(0x24e64,0x24e70),(0x2561c,0x25628),(0x25674,0x2567c),(0x25810,0x25884)],'PreviewsPipeline':[(0x21a8,0x21d0),(0x2340,0x237c),(0xc889c,0xc89c8)],'PreviewsMessagingHost':[(0x3950,0x3954),(0x33b8,0x33c0)]};bodies=[]
for name,rs in regions.items():
 image=images[name]
 for a,b in rs:
  text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert b''.join(words[x] for x in range(a,b,4))==raw;bodies.append({'target':name,'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'pins':pins,'uuids':{n:i.uuid for n,i in images.items()},'import_bindings':bindings,'default_bindings':defaults,'enum_slot_chain':witness,'hosted_default':'display','static_default':'render','selected_bytes_verified':sum(b['bytes'] for b in bodies),'selected_ranges':bodies,'request_metadata_type_resolved':'LocalMacPlatformSupport at first selector','selected_kind_destination':'legacyStaticPreviewMessage in PlatformPreviewUpdateContext','source_only':True,'native_witness_invoked':False,'transport_send_observed':False},indent=2))
