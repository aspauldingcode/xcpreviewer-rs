from pathlib import Path
import subprocess,json,sys,struct,hashlib,re,tempfile
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');subprocess.run(['python3',str(w/'connection-source-verify.py')],check=True,timeout=30,capture_output=True);result=json.loads((w/'source-findings.json').read_text());sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache
c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);rawdir=Path(tempfile.mkdtemp(prefix='pending-reply-source-raw-',dir='/private/tmp'))
for a,b,name in [(0x8e28,0x8e34,'reply-block-thunk'),(0x53e0,0x6048,'reply-callback-path')]:
 p=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(r/'research/raw/service-connection-lifecycle-20261024/analysis.macho')],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',p,re.M)};raw=data[a:b];assert raw==b''.join(words[x] for x in range(base+a,base+b,4));(rawdir/(name+'.raw.s')).write_text(p);result['ranges'].append({'name':name,'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()});result['source_bytes_verified']+=b-a
v=struct.unpack_from('<I',data,0x8e30)[0];n=v&0x3ffffff;assert (v>>26)==5 and 0x8e30+4*(n-(1<<26) if n&(1<<25) else n)==0x53e0
result.update(scope='Original native raw-XPC initialization plus native pending-reply callback path. No receiver installed or native Future invoked. Native runtime guards independently bind activation/cancellation C operation slots to exported SDK functions before class allocation.',offline_got_limitation='Existing cache-v5 helper requires address-diverse authenticated IA pointers and rejects the cancellation GOT slot; no speculative offline decoding used. Runtime equality to dlsym(xpc_connection_activate/xpc_connection_cancel) checks the actual loaded operation pointers instead.')
(w/'source-findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result['source_bytes_verified'])
from reloop.cachebind import export_names
bindings=[]
for address in [0x5368,0x5370,0x5378]:
 word=struct.unpack_from('<I',data,address)[0];assert word>>26==37
 n=word&0x3ffffff;target=base+address+4*(n-(1<<26) if n&(1<<25) else n)
 info=c.stub(target);image,imagebase,_=c.image(info['target']);exports,uid=c.exports(imagebase)
 expected='_swift_release' if address==0x5378 else '_swift_retain'
 assert expected in [x['name'] for x in export_names(exports,info['target']-imagebase)]
 bindings.append({'offset':hex(address),'export':expected,'image':image,'uuid':uid})
result['capture_bindings']=bindings
for address,word in [(0x50c8,0xaa1403f5),(0x50cc,0xaa0203fc),(0x5364,0xaa1503e0),(0x536c,0xaa1c03e0)]:assert struct.unpack_from('<I',data,address)[0]==word
result['retained_self_register_path']={'incoming_self':'x20','saved_self':'x21','save_offset':'0x50c8','retain_argument_offset':'0x5364','retain_call':'0x5368'}
result['scope']='Inherited qualified native raw connection/send/reply source, with additional retain/release bindings within the existing source windows. Nonnil original Swift capture-token ownership is independently observed through the qualified C relay; typed Swift function-value reinterpretation is excluded. Pending native connection retention after original caller reference release and eventual weak-reference clearing are independently observed. This does not claim callback delivery after native connection destruction, notification setters, native Future or final kernel settlement.'
(w/'source-findings.json').write_text(json.dumps(result,indent=2)+'\n')
