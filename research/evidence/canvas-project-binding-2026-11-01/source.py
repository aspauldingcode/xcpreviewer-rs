from pathlib import Path
import struct,hashlib,subprocess,json,re,fcntl,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;rawdir=Path(tempfile.mkdtemp(prefix='canvas-binding-source-raw-',dir='/private/tmp'))
paths={n:Path('/Applications/Xcode.app/Contents/PlugIns')/(n+'.framework/Versions/A')/n for n in ['PreviewsXcode','PreviewsIDEAPI']}
expected={'PreviewsXcode':'ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b','PreviewsIDEAPI':'d3e0ad14a4ea159fde12482d92fb7b7d3f86e4df1578fcef76961a294fbe71f0'}
def image(p):
 b=p.read_bytes();assert b[:4]==bytes.fromhex('cffaedfe');h=struct.unpack_from('<8I',b);assert h[1]==0x100000c and h[4]<512
 at=32;sections=[];uuid=None
 for _ in range(h[4]):
  cmd,size=struct.unpack_from('<II',b,at);assert size>=8 and at+size<=len(b)
  if cmd==0x1b:uuid=b[at+8:at+24].hex()
  if cmd==0x19:
   n=struct.unpack_from('<I',b,at+64)[0];assert 72+n*80<=size
   for i in range(n):
    name,segment,address,length,offset=struct.unpack_from('<16s16sQQI',b,at+72+i*80);sections.append((address,length,offset,name.split(b'\0')[0].decode()))
  at+=size
 assert uuid;return b,sections,uuid
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images=[]
 for name,p in paths.items():
  raw,sections,uuid=image(p);assert hashlib.sha256(raw).hexdigest()==expected[name]
  images.append({'name':name,'path':str(p),'sha256':expected[name],'uuid':uuid,'architecture':'arm64','bytes':len(raw)})
 raw,sections,uuid=image(paths['PreviewsIDEAPI'])
 def read(address,size):
  matches=[s for s in sections if s[0]<=address and address+size<=s[0]+s[1]];assert len(matches)==1
  a,n,off,_=matches[0];return raw[off+address-a:off+address-a+size]
 def word(a):return struct.unpack('<I',read(a,4))[0]
 def branch(a):
  v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
 nm=subprocess.run(['xcrun','nm','--defined-only',str(paths['PreviewsIDEAPI'])],capture_output=True,timeout=20,check=True).stdout.decode();symbols={}
 for line in nm.splitlines():
  m=re.match(r'([0-9a-f]+) \S (.+)',line)
  if m:symbols.setdefault(int(m[1],16),[]).append(m[2])
 calls=[]
 for pc,symbol in [(0x6f90,'_objc_msgSend$standardUserDefaults'),(0x6fc4,'_objc_msgSend$boolForKey:'),(0x6ff4,'_objc_msgSend$buildablesIncludingImplicitDependenciesForWorkspace:scheme:includingPackages:'),(0x7104,'_objc_msgSend$blueprints'),(0x7190,'_objc_msgSend$primaryBuildable'),(0x7378,'_objc_msgSend$isUnitTest'),(0x7428,'_objc_msgSend$blueprint'),(0x745c,'_objc_msgSend$respondsToSelector:')]:
  target=branch(pc);assert symbol in symbols.get(target,[]),(hex(pc),symbol);calls.append({'offset':hex(pc),'selector_stub':symbol,'stub_offset':hex(target)})
 strings=[]
 for address,name in [(0x11cd0,'PreviewsBuildAllPackageTargets'),(0x11cf0,'PreviewsBuildTestTargets'),(0x11f00,'packageProductType')]:
  assert read(address,len(name)+1)==name.encode()+b'\0';strings.append({'offset':hex(address),'value':name})
 # ARM64 generic encodings independently discriminate source branch/register
 # facts; no copied instruction body is retained in the sanitized report.
 v=word(0x6fe8);assert v&31==4 and (v>>5)&31==21 and (v>>10)&0xfff==0
 v=word(0x7050);assert v&0x7f000000==0x34000000 and v&31==21
 target=0x7050+4*((v>>5)&0x7ffff);assert target==0x7250
 assert branch(0x7334)==0x7418
 assert branch(0x7394)==0xff80 and branch(0x739c)==0xff80
 ranges=[]
 for start,end,name in [(0x6f50,0x7418,'buildables'),(0x7418,0x747c,'package-selector-presence')]:
  p=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(start),'--stop-address='+hex(end),str(paths['PreviewsIDEAPI'])],capture_output=True,timeout=20,check=True)
  (rawdir/(name+'.raw.s')).write_bytes(p.stdout)
  words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',p.stdout.decode(),re.M)}
  assert read(start,end-start)==b''.join(words[a] for a in range(start,end,4))
  assert set(words)==set(range(start,end,4)), 'Disassembler output exceeded the requested instruction range'
  ranges.append({'name':name,'start':hex(start),'end_exclusive':hex(end),'bytes':end-start,'sha256':hashlib.sha256(read(start,end-start)).hexdigest()})
 result={'images':images,'source_bytes_verified':sum(x['bytes'] for x in ranges),'ranges':ranges,'selector_calls':calls,'string_anchors':strings,'observed_source_policy':{'all_packages':'Read PreviewsBuildAllPackageTargets; pass its Boolean inverse as includingPackages to scheme/workspace query. When true, enumerate workspace referenced source packages and append each blueprint primaryBuildable. Effective runtime preference not observed.','test_targets':'Read PreviewsBuildTestTargets using a lookup with explicit false fallback. Source filter with true retains elements whose blueprint lacks packageProductType selector; false retains selector-bearing elements or other blueprints that respond to isUnitTest and return false.','package_marker':'Helper checks selector presence only; it does not read the packageProductType value.','runtime':'No native private method called or actual workspace/scheme selection exercised. Source-only policy; no complete graph/project-binding or cross-target parity.'}}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'verified_bytes':result['source_bytes_verified'],'image_uuids':{x['name']:x['uuid'] for x in images}}))
