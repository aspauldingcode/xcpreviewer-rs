from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent
sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks')
images={n:MachO(base/(n+'.framework')/'Versions/A'/n) for n in ['PreviewsPipeline','PreviewsPlatforms','PreviewsMessagingHost','PreviewsFoundationHost']}
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(images['PreviewsPlatforms'].data)=='e155b76d75ef6c37fa6685c8433e8e3cd7ca06f89fd598b5571cf52349d31cbd'
assert sha(images['PreviewsPipeline'].data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
assert sha(images['PreviewsMessagingHost'].data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
def word(p,a):return p.u32(p.file_offset(a))
def call(p,a):
 v=word(p,a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def binding(p,a,stride=12):
 s,ind,libs=tables(p);sec=next(t for t in p.sections if t['address']<=a<t['address']+t['size']);i=index(p,sec,a,stride,ind);n,k,ss,d,v=p.unpack('<IBBHQ',s[0]+16*i);o=s[2]+n;return p.data[o:p.data.index(0,o)].decode()
f=images['PreviewsFoundationHost'];assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
p=images['PreviewsPlatforms'];m=images['PreviewsMessagingHost'];q=images['PreviewsPipeline']
fd=0xd4f78;fields=[m.string(m.relative(fd+16+i*12+8)) for i in range(m.u32(m.file_offset(fd+12)))];assert fields[5]=='update'
assert binding(p,0x46100)=='_$s21PreviewsMessagingHost18ShellUpdatePayloadVMa'
assert binding(p,0x45f38)=='_$s21PreviewsMessagingHost14ServiceMessageV7ContentOMa'
assert word(p,0x34478)==0x528000a2 and call(p,0x3447c)==0x470cc
assert binding(p,0x470cc)=='_swift_storeEnumTagMultiPayload'
assert call(p,0x34490)==0x33134 and call(p,0x3449c)==0x32f64
constructors=[0xb87a8,0xb95e8,0xb9d3c,0xba908,0x1d6174,0x1d6d28,0x1d7978,0x1d8528,0x1dfaa4]
assert all(call(q,a)==0x51dfa8 for a in constructors)
assert 'ShellUpdatePayloadV3pid' in binding(q,0x51dfa8)
assert word(p,0x32c54)==0xf9400868 and word(p,0x32c64)==0xd63f0100
assert call(p,0x332ac)==0x327e0
ranges=[]
for image,a,b,name in [(p,0x342e4,0x344bc,'interfaces.s'),(p,0x327e0,0x32ca4,'send-reply.s'),(p,0x33134,0x332e0,'send-future.s'),(q,0x1dfa78,0x1dfad0,'pipeline-call.s'),(f,0xfc348,0xfc490,'future-success.s'),(m,0x3dbd8,0x3dd54,'unit-reply.s'),(m,0x40f10,0x40fa0,'reply-ownership.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
result={'source_images':{n:{'sha256':sha(p.data),'uuid':p.uuid} for n,p in images.items()},'ranges':ranges,'verified_bytes':sum(t['bytes'] for t in ranges),'content_cases':fields,'pipeline_constructor_callers':list(map(hex,constructors)),'scope':'Modern update tag5/Future send; primitive-send witness at slot16; native Unit reply and success predicate; native TransportReply copy/destroy. Owned ABI-shaped transport boundary supplies the witness, without a registered native daemon conformance. Runtime probe separately invokes actual modern update and controlled immediate/delayed Unit replies. No daemon routing/application/resource settlement observed.'}
(w/'source-findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result['verified_bytes'])
