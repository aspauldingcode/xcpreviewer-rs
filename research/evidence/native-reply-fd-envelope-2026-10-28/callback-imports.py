from pathlib import Path
import struct,sys,json
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re');from reloop.cachebind import Cache,export_names
c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;rows=[]
for offset in range(0x53e0,0x6048,4):
 word=struct.unpack('<I',c.read(base+offset,4))[0]
 if word>>26 not in [5,37]:continue
 n=word&0x3ffffff;target=base+offset+4*(n-(1<<26) if n&(1<<25) else n)
 try:
  s=c.stub(target);p,b,_=c.image(s['target']);t,u=c.exports(b);names=[x['name'] for x in export_names(t,s['target']-b)]
 except ValueError:continue
 if any('xpc' in x.lower() or 'objc' in x.lower() for x in names):rows.append({'offset':hex(offset),'exports':names,'image':p,'uuid':u})
print(json.dumps(rows,indent=2));Path(__file__).with_name('callback-imports.json').write_text(json.dumps(rows,indent=2)+'\n')
