from pathlib import Path
import sys,struct,hashlib,json,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;trie,uuid=c.exports(base);assert uuid=='fffb683f59433c2591b272d6e5174fa3';data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
def branch(o):
 v=struct.unpack_from('<I',data,o)[0];assert v>>26 in [5,37];n=v&0x3ffffff;return base+o+4*(n-(1<<26) if n&(1<<25) else n)
expected={0x7cd0:'_swift_allocObject',0x7ce0:'_swift_weakInit',0x7d40:'__Block_copy',0x7d50:'_swift_unknownObjectRetain',0x7d58:'_swift_release',0x7d64:'_xpc_connection_set_event_handler',0x7d6c:'__Block_release',0x6e14:'_objc_opt_self',0x88b4:'_swift_allocObject',0x88a4:'_xpc_connection_enable_sim2host_4sim',0x538c:'_xpc_connection_send_message_with_reply'}
bindings=[]
for o,name in expected.items():
 info=c.stub(branch(o));path,b,_=c.image(info['target']);t,u=c.exports(b);assert name in [x['name'] for x in export_names(t,info['target']-b)];bindings.append({'call':hex(o),'export':name,'image':path,'uuid':u})
for o,target in [(0x88a8,0x6e00),(0x88c4,0x7c84),(0x7e28,0x6e00),(0x7e40,0x7c84),(0xa140,0x37c4),(0xa1f8,0x4dfc),(0xa244,0x50a4),(0x4e2c,0x3d94)]:assert branch(o)==base+target
for o,word in [(0x7ca0,0xf900369f),(0x7cbc,0xf9000a80),(0x88ac,0x52800e01),(0x88b0,0x528000e2),(0x7e2c,0x52800e01),(0x7e30,0x528000e2)]:assert struct.unpack_from('<I',data,o)[0]==word
rawdir=Path(tempfile.mkdtemp(prefix='native-local-source-raw-',dir='/private/tmp'));ranges=[];image=r/'research/raw/service-connection-lifecycle-20261024/analysis.macho'
for a,b,name in [(0x6e00,0x6e24,'class-metadata'),(0x7c84,0x7d88,'raw-initializer'),(0x7d88,0x7e44,'ordinary-caller'),(0x8800,0x88d4,'simulator-caller'),(0x37c4,0x3a70,'invalidate'),(0x3d94,0x4050,'activate-body'),(0x4dfc,0x4e30,'activate-wrapper'),(0x50a4,0x53e0,'send-reply'),(0xa12c,0xa254,'outer-forwarders')]:
 p=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(image)],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',p,re.M)};raw=data[a:b];assert raw==b''.join(words[x] for x in range(base+a,base+b,4));(rawdir/(name+'.raw.s')).write_text(p);ranges.append({'name':name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
pins={'PreviewsMessagingHost':'0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c','PreviewsFoundationHost':'1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d','PreviewsPlatforms':'e155b76d75ef6c37fa6685c8433e8e3cd7ca06f89fd598b5571cf52349d31cbd'}
for n,h in pins.items():assert sha((Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(n+'.framework/Versions/A')/n).read_bytes())==h
result={'services_uuid':uuid,'services_text_sha256':sha(data),'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'bindings':bindings,'xcode_file_sha256':pins,'scope':'Plain raw-XPC initializing constructor, class accessor, allocation call sites and native activate/send/invalidate boundaries. Ordinary caller does not apply the simulator operation before initialization; simulator caller does. Selected ranges and runtime controls do not recover the full outer service/daemon constructor, receiver registration or resource settlement.'};(w/'source-findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result['source_bytes_verified'])
