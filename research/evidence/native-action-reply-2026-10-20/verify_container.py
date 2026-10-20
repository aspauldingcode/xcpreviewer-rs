"""Check a local mapped container against independently captured export probes."""
from pathlib import Path
import json,struct,sys

def verify(folder,blob):
 m=json.loads((folder/'mapped.json').read_text());assert len(blob)>=64 and blob[:6]==b'\x7fELF\x02\x01'
 assert struct.unpack_from('<H',blob,18)[0]==183
 off=struct.unpack_from('<Q',blob,32)[0];size,count=struct.unpack_from('<HH',blob,54);assert size==56 and count==len(m['segments'])<=32 and off+size*count<=len(blob)
 ranges=[]
 for i,s in enumerate(m['segments']):
  kind,flags,offset,address,_,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',blob,off+i*size)
  assert kind==1 and filesz==memsz==s['size'] and address==int(s['address'],16) and align==1 and offset+filesz<=len(blob)
  assert blob[offset:offset+filesz]==(folder/s['file']).read_bytes();ranges.append((address,address+filesz,offset))
 for i,s in enumerate(m['symbols']):
  a=int(s['address'],16);r=[r for r in ranges if r[0]<=a and a+32<=r[1]];assert len(r)==1
  start=r[0][2]+a-r[0][0];assert blob[start:start+32]==(folder/('symbol-%d.bin'%i)).read_bytes()
 return ranges

if __name__=='__main__':
 f=Path(sys.argv[1]);b=(f/'BaseBoard-mapped-v2.elf').read_bytes();ranges=verify(f,b)
 m=json.loads((f/'mapped.json').read_text());a=int(m['symbols'][0]['address'],16);r=next(r for r in ranges if r[0]<=a<r[1]);p=r[2]+a-r[0]
 changed=bytearray(b);changed[p]^=1;wrongmap=bytearray(b);struct.pack_into('<Q',wrongmap,64+16,ranges[0][0]+4)
 rejected=0
 for mutant in [bytes(changed),b[:100],bytes(wrongmap)]:
  try:verify(f,mutant)
  except (AssertionError,ValueError,struct.error):rejected+=1
 assert rejected==3
 print(json.dumps({'mapped_segments_all_bytes_equal':len(ranges),'direct_export_probe_bytes_equal':32*len(m['symbols']),'container_mutants_rejected':rejected}))
