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
imports={hex(a):binding(a) for a in [0x12fa94,0x12fb84]};assert 'format9arguments' in imports['0x12fa94'];assert imports['0x12fb84']=='_$sSS6appendyySSF'
# Optional String data word selects presence, not emptiness.
assert word(0x5f47c)&0xff00001f==0xb5000001;conditional(0x5f47c,0x5f4a4)
assert word(0x5f4ec)&0xff00001f==0xb5000001;conditional(0x5f4ec,0x5f514)
# Optional option bits nil tag1 and severity nil tag2 select cause only if nil.
assert word(0x5f634)==0x7100051f;conditional(0x5f638,0x5f668)
assert word(0x5f6d8)==0x7100091f;conditional(0x5f6dc,0x5f70c)
assert word(0x5f618)==0xf9401ee9 and word(0x5f64c)==0xf9401ee9
assert word(0x5f6bc)==0xf94022e9 and word(0x5f6f0)==0xf94022e9
# Fixed %@: %@ format literal in x4 and native String(format:arguments:) edge.
assert [word(a) for a in range(0x5f594,0x5f5a0,4)]==[0xd28804a4,0xf2a40744,0xf2c804a4];assert call(0x5f5b0)==0x5e0b0 and call(0x5e158)==0x12fa94
conditional(0x5e0d0,0x5e160);conditional(0x5e0d8,0x5e174)
# Both type descriptions are read, period appended, then cause appended.
assert word(0x5f868)==0x528005c0 and call(0x5f870)==0x12fb84 and call(0x5f8a0)==0x12fb84
assert word(0x5f84c)==0xf9402ec8 and word(0x5f884)==0xf9402ec8
# Declared wrapper additionalDiagnostics witness maps to the shared nil body.
assert [word(a) for a in range(0x4b2c,0x4b38,4)]==[0xd2800000,0xd2800001,0xd65f03c0]
# Resolve symbol identity without treating it as a callable Swift prototype.
nm=subprocess.run(['xcrun','nm','-n',str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();assert any(line.startswith('0000000000004b2c ') and 'UnderlyingErrorWrapper' in line and 'additionalDiagnostics' in line for line in nm.splitlines())
ranges=[]
for a,b in [(0x5f444,0x5f728),(0x5e0b0,0x5e1a0),(0x5f824,0x5f8c4),(0x4b2c,0x4b38)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'imports':imports,'main_first_present':['highValueTitle','lowValueTitle','options','severity'],'additional_info_format':'%@: %@','type_description_separator':'.','wrapper_additional_diagnostics':None,'native_private_getters_invoked':False,'full_diagnostics_formatter_implemented':False,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges)}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
