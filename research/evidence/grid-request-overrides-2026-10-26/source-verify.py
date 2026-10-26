from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest()
m=MachO(Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline'))
assert sha(m.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def binding(a):
 s,ind,libs=tables(m);sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()
assert call(0x6f610)==0x2b7988
assert call(0x6fee8)==0x520f3c and word(0x6feec)==0x7100041f and word(0x6fef0)==0x540028e1 # grid tag1
assert word(0x6fefc)==0xf85303a0 and word(0x6ff10)==0xd63f0100 # copy enum payload into grid group
assert word(0x6ff1c)==0xb40028c8 # empty tuple array -> empty overrides
for site in [0x70028,0x70050,0x70118,0x70244]:assert call(site)==0x51e044
assert binding(0x51e044)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV2idAC2IDVvg'
for site in [0x700f4,0x70200]:assert call(site)==0x51dffc
assert binding(0x51dffc)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV010associatedF3IDsShyAC2IDVGvg'
for site in [0x7008c,0x701b8,0x702fc]:assert call(site)==0x51f8bc
assert binding(0x51f8bc)=='_$sSQ2eeoiySbx_xtFZTj'
assert word(0x700bc)==0x3707f674 and word(0x701cc)==0x3707ebfc and word(0x70310)==0x370006b4
assert call(0x703d4)==0x1f2cc # only nonmatching tuple copied to output in input order
assert word(0x703e8)==0x17fffed9 and word(0x6ff98)==0x910006d6
assert word(0x704ec)==0xb9803118 and word(0x70538)==0xf9400af8 # tuple member offset, override count
assert call(0x705cc)==0x520dbc and binding(0x520dbc)=='_swift_arrayInitWithCopy'
assert word(0x705e8)==0xf9000a68 and word(0x705ec)==0x17ffffae # append count then next tuple
ranges=[]
for a,b,name in [(0x6f610,0x6f614,'effective-call.s'),(0x6fee0,0x705f0,'grid-filter-flatten.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_previewRequests_invoked':False,'scope':'grid-tag branch: equal ID OR either direct association excludes tuple; flatten survivor override arrays in source order; all mode/capability/request/runtime behavior excluded'}
(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
