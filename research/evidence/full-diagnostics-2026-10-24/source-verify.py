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
imports={hex(a):binding(a) for a in [0x1305d4,0x1305a4,0x12f974,0x12fb84]}
assert 'replacingOccurrences2of4with7options5range' in imports['0x1305d4']
assert 'components11separatedBy' in imports['0x1305a4']
assert 'joined9separator' in imports['0x12f974']
assert imports['0x12fb84']=='_$sSS6appendyySSF'
assert word(0x5bd98)==0xf9402c28
for a,target,opcode in [(0x5bdb4,0x5bdd0,0xb5000001),(0x5bdcc,0x5be08,0xb4000001),(0x5be1c,0x5be50,0xb4000001),(0x5be64,0x5be98,0xb4000001)]:
 assert word(a)&0xff00001f==opcode;conditional(a,target)
for a in [0x5bdd0,0x5b0a4]:assert word(a)==0x52840748
for a in [0x5be2c,0x5be74,0x5b104,0x5b130]:assert word(a)==0x52814140
for a in [0x5be98,0x5b14c]:assert word(a)==0x528dcb88
for a in [0x5bea4,0x5b158,0x10ccd8]:assert word(a)==0x52800148
assert call(0x5bee4)==call(0x5b198)==0x1305d4
assert call(0x60868)==0x5b054 and call(0x63684)==0x5f90c and call(0x5f90c)==0x5f994
assert word(0x5f9b4)==0x9100a280 and word(0x5f9c0)==0xf9403ac8
assert word(0x5f9e0)==0xaa1303e0 and word(0x5f9ec)==0xf9403b08
assert m.data[m.file_offset(0x143a10):m.file_offset(0x143a10)+38]==b'\n\n==================================\n\n'
assert word(0x5fa24)==0xd28004c0 and word(0x5fa3c)==0x52840f80 and word(0x5fa40)==0x72a00400
assert word(0x5fa48)==0xd2800002 and call(0x5fa54)==0x10ccac
assert call(0x10cd04)==0x1305a4 and call(0x10ce4c)==0x12f974
conditional(0x10cd58,0x10cd68)
ranges=[]
for a,b in [(0x5bd74,0x5bf18),(0x5b054,0x5b1dc),(0x5f994,0x5fab0),(0x10ccac,0x10ce8c),(0x60834,0x6087c),(0x63684,0x63688),(0x5f90c,0x5f910)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'imports':imports,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'leaf_title_separator':': ','optional_section_separator':'\n\n','literal_backslash_n_replaced_with_lf':True,'wrapper_cause_line_prefix':'|  ','wrapper_divider':'\n\n==================================\n\n','private_getters_invoked':False}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
