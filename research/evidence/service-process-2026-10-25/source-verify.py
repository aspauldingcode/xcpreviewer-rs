from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
sha=lambda b:hashlib.sha256(b).hexdigest();base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');m=MachO(base/'PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO(base/'PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c' and sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(image,a):
 v=image.u32(image.file_offset(a));assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def fields(a):
 kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
def binding(image,a,stride=12):
 s,ind,libs=tables(image);sec=next(t for t in image.sections if t['address']<=a<t['address']+t['size']);i=index(image,sec,a,stride,ind);n,k,ss,d,v=image.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return image.data[o:image.data.index(0,o)].decode()
assert fields(0xd52e8)==['auditToken','pid'] and fields(0xd5648)==['discriminant','auditToken','pid'] and fields(0xd567c)==['auditToken','pid']
assert word(0x694b8)==0x52800048 and call(m,0x694d8)==0xb190c and call(m,0x69500)==0xb25fc
assert word(0x69534)==0x7100051f and word(0x69540)==0x52800048 and word(0x695ac)==0x52800028
assert call(m,0x69564)==call(m,0x695f0)==0xb190c
assert word(0x6956c)==0xb5fff9f5 and word(0x695f8)==0xb5fff595
assert word(0x666a8)==0x52800048 and call(m,0x66698)==0xb20ec and call(m,0x666c8)==0xb1900
assert binding(m,0xb20ec)=='_$sSo13audit_token_ta22PreviewsFoundationHostE3pids5Int32Vvg'
assert call(f,0x921ac)==0x130f7c and binding(f,0x130f7c)=='_audit_token_to_pid'
assert binding(m,0xe4758,8)=='_$ss5Int32VN'
assert f.u32(f.file_offset(0xaaa9c))==0xf100211f and f.u32(f.file_offset(0xaaaa0))==0x540000c1
assert call(f,0xaaa78)==0x5e904
# Token encoder emits literal val and the eight words in their stored order.
assert f.u32(f.file_offset(0x9f930))==0x528c2ec8 and f.u32(f.file_offset(0x9f934))==0x72a00d88
assert [f.u32(f.file_offset(a)) for a in range(0x9f8f4,0x9f904,4)]==[0x29046418,0x29056817,0x29066c16,0x29077015]
routes=[('connect',5,3,0x60088,0x600ac,0x600cc,0x60104),('stop',9,7,0x5fed8,0x5ff00,0x5ff20,0x5ff58),('kill',10,8,0x6021c,0x6023c,0x6025c,0x60294)]
for name,kind,content,dest,witness,decode,store in routes:
 assert fields(0xd4ec0)[kind]==fields(0xd4f78)[content]==name
 assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a+2*kind))[0]==dest
 assert 0x5e96c+4*m.data[m.file_offset(0xba16d)+content]==0x5e96c
 assert call(m,witness)==0x5ef1c and call(m,decode)==0xb1c24 and (word(store)>>5)&0xffff==content
assert call(m,0x5e97c)==0x5ef1c and call(m,0x5e998)==0xb1c18
regions=[('Foundation',f,0x9217c,0x921c0),('Messaging',m,0x66510,0x66718),('Messaging',m,0x69440,0x6965c),('Messaging',m,0x661cc,0x66208),('Messaging',m,0x5fed8,0x5ff60),('Messaging',m,0x60088,0x6010c),('Messaging',m,0x6021c,0x6029c),('Messaging',m,0x5e96c,0x5e9a0),('Foundation',f,0x9f884,0x9f9e0),('Foundation',f,0xaaa40,0xaab10)]
ranges=[]
for name,image,a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)});(w/(name+'-'+hex(a)+'.s')).write_text(text)
out={'images':{'Messaging':{'sha256':sha(m.data),'uuid':m.uuid},'Foundation':{'sha256':sha(f.data),'uuid':f.uuid}},'process_cases':fields(0xd52e8),'process_keys':fields(0xd5648),'audit_token_key':'val','audit_token_words':8,'legacy_pid_fallback':True,'public_pid_import':binding(f,0x130f7c),'pid_import':binding(m,0xb20ec),'pid_metadata':binding(m,0xe4758,8),'routes':[x[0] for x in routes],'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_functions_invoked':False,'native_process_action_performed':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
