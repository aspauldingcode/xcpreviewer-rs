from pathlib import Path
import sys,subprocess,re,json,hashlib
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');m=MachO(base/'PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO(base/'PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
s,ind,libs=tables(m);sec=next(t for t in m.sections if t['address']<=0xb1cfc<t['address']+t['size']);i=index(m,sec,0xb1cfc,12,ind);o=m.unpack('<IBBHQ',s[0]+16*i)[0]+s[2];assert m.data[o:m.data.index(0,o)].decode()=='_$s22PreviewsFoundationHost8CallsiteVMa'
assert [f.u32(f.file_offset(a)) for a in range(0x490ac,0x490c4,4)]==[0xa9000500,0x39004102,0xa9019103,0xa9029905,0x3900e107,0xd65f03c0]
ranges=[]
for image,a,b in [(m,0x3fb40,0x3fc80),(m,0x40114,0x4018c),(f,0x490ac,0x490ec)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/(image.path.name+'-'+hex(a)+'.s')).write_text(text);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
assert sum(x['bytes'] for x in ranges)==504
(w/'extra-findings.json').write_text(json.dumps({'ranges':ranges,'bytes_verified':504,'callsite_native_constructor':True,'handler_returns_owned_function_context_pair':True,'capture_copies_native_reply_and_callsite':True,'source_scope':'Constructor stores exact StaticString/line/column fields; makeEncodedReplyHandler copies TransportReply and Callsite into captured context and returns native thunk/context. Runtime size/offset and function-path guards independently execute. No native terminal error object or exactly-once lifetime claimed.'},indent=2)+'\n');print('Verified504 additional source bytes')
