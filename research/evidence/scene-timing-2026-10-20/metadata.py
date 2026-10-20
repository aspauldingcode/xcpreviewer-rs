from pathlib import Path
import json,struct
p=Path('/Users/8amps/xcpreviewer-rs/research/raw/scene-timing-20261020/mapped');m=json.loads((p/'mapped.json').read_text());slide=int(m['slide'],16)
def read(a,n):
 for s in m['segments']:
  start=int(s['address'],16)
  if start<=a and a+n<=start+s['size']:return (p/s['file']).read_bytes()[a-start:a-start+n]
 raise ValueError(hex(a))
def string(a):return read(a,min(100, next(int(s['address'],16)+s['size']-a for s in m['segments'] if int(s['address'],16)<=a<int(s['address'],16)+s['size']))).split(b'\0')[0].decode()
base=int(m['segments'][0]['address'],16);header=read(base,32);n=struct.unpack_from('<I',header,16)[0];a=base+32;section=None
for _ in range(n):
 cmd,size=struct.unpack('<II',read(a,8))
 if cmd==0x19:
  ns=struct.unpack_from('<I',read(a,72),64)[0]
  for i in range(ns):
   b=read(a+72+i*80,80)
   if b[:16].split(b'\0')[0]==b'__swift5_fieldmd':section=struct.unpack_from('<QQ',b,32)
 a+=size
assert section
at=section[0]+slide;end=at+section[1];found=[]
while at+16<=end:
 _,_,kind,size,count=struct.unpack('<iiHHI',read(at,16))
 assert count<1000 and (size==12 or count==0)
 names=[]
 for i in range(count):
  field=at+16+i*size+8;rel=struct.unpack('<i',read(field,4))[0];names.append(string(field+rel))
 if names==['fenced','async'] or set(names)=={'preferencesResolved','confirmReadyForDisplayAfterSceneResize','hardwareEvent'}:found.append({'descriptor_unslid':hex(at-slide),'kind':kind,'names':names})
 at+=16+count*size
assert any(f['names']==['fenced','async'] for f in found)
assert any(set(f['names'])=={'preferencesResolved','confirmReadyForDisplayAfterSceneResize','hardwareEvent'} for f in found)
assert struct.unpack('<q',read(0x2a447f7a0,8))[0]==0
print(json.dumps({'domains':found,'seed_initial_observed_in_owned_process':0,'seed_instructions':['ADRP','LDR','ADD #1','STR global','STR result','RET'],'scope':'Source constructor; no native Swift call or concurrent uniqueness claim'}))
