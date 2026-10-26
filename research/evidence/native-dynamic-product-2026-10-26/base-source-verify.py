from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest();base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');m=MachO(base/'PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO(base/'PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c' and sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(p,a):return p.u32(p.file_offset(a))
def call(p,a):
 v=word(p,a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def binding(p,a,stride=12):
 s,ind,libs=tables(p);sec=next(t for t in p.sections if t['address']<=a<t['address']+t['size']);i=index(p,sec,a,stride,ind);n,k,ss,d,v=p.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return p.data[o:p.data.index(0,o)].decode()
def fields(p,a):
 _,size,n=p.unpack('<HHI',p.file_offset(a+8));assert size==12;return [p.string(p.relative(a+16+i*size+8)) for i in range(n)]
assert fields(m,0xd39e0)==['plist'] and fields(f,0x159c08)==['serializableDictionary']
assert f.data[f.file_offset(0x149ca0):f.file_offset(0x149ca0)+8]==b'SDySSypG'
assert binding(m,0xb1990)=='_$s22PreviewsFoundationHost12PropertyListVMa'
assert call(m,0x1d650)==call(m,0x1d694)==0xb1990
assert word(m,0x1d65c)==0xf9401108 and word(m,0x1d668)==0xd63f0100 # initializeWithTake, no value-key access
assert word(m,0x1d6a0)==0xf9400903 and word(m,0x1d6b4)==0xd61f0060 # initializeWithCopy, whole plist
assert [word(m,a) for a in range(0x1d564,0x1d574,4)]==[0xd28c2ec0,0xf2aead80,0xf2c00ca0,0xd2fca001] # raw key value
assert binding(m,0xe4f48,8)=='_$s22PreviewsFoundationHost12PropertyListV14unarchiveValue3forxAA0dE3Key_p_tKAA0dE13RepresentableRzlF'
assert binding(m,0xe4f70,8)=='_$s22PreviewsFoundationHost12PropertyListV22unarchiveOptionalValue3forxSgAA0dE3Key_p_tKAA0dE13RepresentableRzlF'
assert call(m,0x1d588)==call(m,0x1d5a4)==0x1d5b0 and word(m,0x1d604)==0xd63f0260
assert word(f,0x5eca4)==0x36000341 and word(f,0x5eccc)==0xb40002c8 # missing -> error path
assert call(f,0x5ecec)==0x61d70
assert word(f,0x60488)==0x36000301 and word(f,0x604b0)==0xb4000288 # missing -> nil path
assert word(f,0x60518)==0xd2800000 and word(f,0x6051c)==0xd2800001
assert call(f,0x604d0)==0x61d70 and word(f,0x604d8)==0xb4000335 # present errors propagate
assert call(f,0x61dc4)==0x131270 and binding(f,0x131270)=='_swift_dynamicCast'
assert binding(f,0x170fe0,8)=='_$sSSN' and word(f,0x61dc8)==0x36000060
ranges=[]
for p,a,b,name in [(m,0x1d54c,0x1d6b8,'box-codec.s'),(f,0x5ec38,0x5eda4,'required-string.s'),(f,0x6041c,0x60558,'optional-string.s'),(f,0x61d70,0x61e60,'string-conversion.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':p.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'source_images':{p.path.name:{'sha256':sha(p.data),'uuid':p.uuid} for p in [m,f]},'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_box_getter_invoked':False,'scope':'whole dictionary box wire identity; delegated required/optional value access; String cast specialization; portable outer-collision restriction separate from native'}
(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
