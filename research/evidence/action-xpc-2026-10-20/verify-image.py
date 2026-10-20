from pathlib import Path
import json,struct,hashlib,sys
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(sys.argv[1]);m=r/'research/raw/action-reply-20261020/mapped';b=(m/'BaseBoard-mapped-v2.elf').read_bytes();assert hashlib.sha256(b).hexdigest()=='3c8e97d02afbbf1abd44108642e3cdeb38d73a508fa77d29741e8969058f1190'
v=json.loads((m/'mapped.json').read_text());off=struct.unpack_from('<Q',b,32)[0];sz,n=struct.unpack_from('<HH',b,54);ranges=[]
for i,s in enumerate(v['segments']):
 _,_,o,a,_,f,mem,_=struct.unpack_from('<IIQQQQQQ',b,off+i*sz);assert f==mem==s['size'];assert b[o:o+f]==(m/s['file']).read_bytes();ranges.append((a,a+f,o))
probes=json.loads((w/'probes.json').read_text())
for x in json.loads((w/'metadata.json').read_text()):
 assert x['uuid']==v['uuid'];a=int(x['address'],16);lo,hi,o=next(t for t in ranges if t[0]<=a and a+32<=t[1]);native=bytes.fromhex(x['prefix32']);g=probes[x['address']];data=next(json.loads(c['text'])['data'] for c in g['content'] if c['type']=='text');assert native==bytes(data)==b[o+a-lo:o+a-lo+32]
print(json.dumps({'mapped_bytes_verified':sum(s['size'] for s in v['segments']),'native_ghidra_probe_bytes_equal':128}))
