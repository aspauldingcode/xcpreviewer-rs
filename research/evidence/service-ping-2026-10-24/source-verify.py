from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest()
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def fields(a):
 kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
def binding(image,a,stride=12):
 s,ind,libs=tables(image);sec=next(t for t in image.sections if t['address']<=a<t['address']+t['size']);i=index(image,sec,a,stride,ind);n,k,ss,d,v=image.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return image.data[o:image.data.index(0,o)].decode()
assert fields(0xd4ec0)[0]=='ping' and fields(0xd4f78)[12]=='ping'
assert 0x5fce4+4*m.unpack('<H',m.file_offset(0xba17a))[0]==0x5ff60
assert 0x5e96c+4*m.data[m.file_offset(0xba16d)+12]==0x5e9f0
# Raw-kind ping registers are set before dispatch, case0 goes straight to ret.
assert word(0x60760)==0x528d2e00 and word(0x60764)==0x72acedc0
assert 0x60784+4*m.data[m.file_offset(0xba196)]==0x60870 and word(0x60870)==0xd65f03c0
# Required root and optional payload identifier decoding precede kind dispatch.
assert call(0x5f754)==call(0x5f7ac)==0xb190c and call(0x5fc3c)==0xb1948
assert call(0x5ff74)==0x5e420 and word(0x5ff88)==0x52800182
assert call(0x5ff8c)==0xb27dc and call(0x5ff90)==0x5fc60
assert call(0x5e9f8)==0xb1954 and call(0x5e9fc)==0x5ece4 and call(0x5ed18)==0xb1900
imports={hex(a):binding(m,a) for a in [0xb190c,0xb1948,0xb1954,0xb1900,0xb27dc]}
assert imports['0xb1954']=='_$s22PreviewsFoundationHost12PropertyListV5emptyACvgZ';assert imports['0xb27dc']=='_swift_storeEnumTagMultiPayload'
assert f.u32(f.file_offset(0x9accc))==0xf00006a0 and f.u32(f.file_offset(0x9acd0))==0xf946f000
assert fields(0xd5434)==['messageType','payload']
empty_array=binding(f,0x171de0,8);assert empty_array=='__swiftEmptyArrayStorage'
# Foundation empty getter uses the empty-array literal constructor.
v=f.u32(f.file_offset(0x9acd4));n=v&0x3ffffff;assert 0x9acd4+4*(n-(1<<26) if n&(1<<25) else n)==0xe144
regions=[('Messaging',m,0x5f684,0x5f840),('Messaging',m,0x5fc0c,0x5fce4),('Messaging',m,0x5ff60,0x5ff94),('Messaging',m,0x5e928,0x5e96c),('Messaging',m,0x5e9f0,0x5ea00),('Messaging',m,0x5ece4,0x5ed44),('Messaging',m,0x60758,0x60784),('Messaging',m,0x60870,0x60874),('Foundation',f,0x9acbc,0x9ace8)]
ranges=[]
for name,image,a,b in regions:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'image':name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
 # Source bytes/disassembly remain local, never copied to public bundle.
 (w/(name+'-'+hex(a)+'.s')).write_text(text)
out={'images':{'Messaging':{'sha256':sha(m.data),'uuid':m.uuid},'Foundation':{'sha256':sha(f.data),'uuid':f.uuid}},'wire_kind':'ping','kind_internal_ordinal':0,'content_internal_ordinal':12,'root_keys':['messageType','payload'],'identifier_key':'__unique_service_message_identifier','content_specific_fields':[],'imports':imports,'empty_literal_input':empty_array,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_functions_invoked':False,'native_ping_delivery_observed':False}
p=w/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
