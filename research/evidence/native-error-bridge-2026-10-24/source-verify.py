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
assert word(0x1b18)==0x92800003 and word(0x1b1c)==0xaa1303e4 and call(0x1b20)==0x131c20
assert word(0x5ddd0)==0xf9400ec8 and word(0x5ddf4)==0xf94012c8
assert word(0x5dde0)==0xb40000a1;conditional(0x5dde0,0x5ddf4)
assert word(0x5de10)==0xb50000c1;conditional(0x5de10,0x5de28)
assert word(0x5de18)==0x91274108 and word(0x5de40)==0x9127c108
assert m.data[m.file_offset(0x1439d0):m.file_offset(0x1439d0)+24]==b'Unexpected preview error'
assert m.data[m.file_offset(0x1439f0):m.file_offset(0x1439f0)+20]==b'UVHumanReadableError'
assert word(0x5de50)==0xf9403ec9 and word(0x5de60)==0xd63f0120
assert word(0x5deb4)==0x52800041 and call(0x5def4)==0x132600
nm=subprocess.run(['xcrun','nm','-n',str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode()
for address,name in [('0000000000001aec','uv_errorWithUserInfo:'),('0000000000131c20','_objc_msgSend$initWithDomain:code:userInfo:'),('0000000000132600','_objc_msgSend$uv_errorWithUserInfo:')]:assert any(line.startswith(address+' ') and name in line for line in nm.splitlines())
ranges=[]
for a,b in [(0x1aec,0x1b40),(0x5dd5c,0x5df2c)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'factory_domain_runtime':'com.apple.Previews','factory_code':-1,'title_order':['highValueTitle','lowValueTitle','Unexpected preview error'],'archive_key':'UVHumanReadableError','native_swift_getter_invoked':False}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
