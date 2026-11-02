from pathlib import Path
import struct,sys,subprocess,re,json,hashlib
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re/reloop')
from cachebind import Cache
w=Path(__file__).parent;c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x1b520f000
raw_exports,uuid=c.exports(base)
assert uuid=='90f7fa24a2803e8aa62d148b11bfc28d' and c.image(base)[0]=='/System/Library/Frameworks/SwiftUI.framework/Versions/A/SwiftUI'
ranges=[('body-closure',0x1060280,0x1060288),('body-closure-helper',0x106016c,0x1060280),('body-destroy',0xc545c,0xc5460),('existential-destroy',0xe5c74,0xe5cb8),('body-init',0x10602e0,0x1060344),('body-getter',0x1060458,0x1060464),('existential-copy',0x167de8,0x167e44),('body-metadata',0x10605b0,0x10605c0),('preview-init',0x105f5a4,0x105f830)]
rows=[]
for name,start,end in ranges:
 address=base+start;raw=c.read(address,end-start);n=len(raw);fo=0x1000
 header=struct.pack('<8I',0xfeedfacf,0x100000c,0,1,1,152,0,0)
 segment=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',address,n,fo,n,7,5,1,0)
 section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',address,n,fo,2,0,0,0x80000400,0,0,0)
 p=w/(name+'.macho');p.write_bytes((header+segment+section).ljust(fo,b'\0')+raw)
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble',str(p)],capture_output=True,check=True,timeout=10).stdout.decode();(w/(name+'.raw.s')).write_text(text)
 words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)}
 assert raw==b''.join(words[a] for a in range(address,address+n,4))
 rows.append({'name':name,'offset':hex(start),'bytes':n,'sha256':hashlib.sha256(raw).hexdigest()})
(w/'source-ranges.json').write_text(json.dumps(rows,indent=2)+'\n')
print((w/'body-getter.raw.s').read_text());print((w/'body-init.raw.s').read_text()[:4200])
