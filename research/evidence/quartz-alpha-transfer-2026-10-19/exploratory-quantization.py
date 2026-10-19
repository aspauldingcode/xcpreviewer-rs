"""Post-acquisition rejected hypotheses; no fitting or replacement goldens."""
from pathlib import Path
import struct,json
from predictions import norm
p=Path(__file__).resolve().parent;raw=(p/'owned-documents'/'route0-readback.raw').read_bytes();rows=[]
for model in ['half','nearest512','floor512']:
 count=0
 for y in range(3):
  for x in range(768):
   a=norm(x//3);v=struct.unpack('<e',struct.pack('<e',a))[0] if model=='half' else round(a*512)/512 if model=='nearest512' else int(a*512)/512;expected=struct.pack('<4f',*[v if c==x%3 else 0 for c in range(3)],v);count+=sum(a!=b for a,b in zip(raw[y*12352+x*16:y*12352+x*16+16],expected))
 rows.append({'post_acquisition_hypothesis':model,'active_byte_mismatches':count,'qualified':False})
print(json.dumps({'hypotheses':rows,'phase':'exploratory_after_acquisition','used_as_goldens':False,'internal_datatype_proven':False}))
