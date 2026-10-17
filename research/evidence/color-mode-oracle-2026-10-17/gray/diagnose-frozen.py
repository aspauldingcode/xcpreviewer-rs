"""Compare every byte to unchanged predeclared patterns; observation is not a golden."""
import json,struct,hashlib,sys
from pathlib import Path
from record_admit import parsed,record,need
p=Path(__file__).parent;f=parsed((p/'fixture-record.json').read_text());raw,pid=record(f);rows=[parsed(x) for x in raw.decode().splitlines()];out=[]
for r in rows:
 data=(p/'owned-documents'/r['file']).read_bytes();need(len(data)==4096)
 high=r['phase']==1;candidates=[('exact',0.5 if high else 0.25)]+([('quantized8',128/255 if high else 64/255)] if r['mode']==0 else [])
 comparisons=[]
 for label,value in candidates:
  expected=bytearray([0xa5]*4096);pixel=struct.pack('<4f',value,value,value,1)
  for y in range(9):expected[y*288:y*288+272]=pixel*17
  mismatch=[i for i,(a,b) in enumerate(zip(data,expected)) if a!=b]
  comparisons.append({'candidate':label,'mismatch_bytes':len(mismatch),'first_mismatch':mismatch[0] if mismatch else None})
 padding=[data[y*288+272:y*288+288] for y in range(9)];need(all(x==b'\xa5'*16 for x in padding) and data[2592:]==b'\xa5'*1504)
 alpha=[data[y*288+x*16+12:y*288+x*16+16] for y in range(9) for x in range(17)];need(all(x==struct.pack('<f',1) for x in alpha))
 out.append({'mode':r['mode'],'phase':r['phase'],'route':r['route'],'file':r['file'],'sha256':hashlib.sha256(data).hexdigest(),'image_storage':{k:v for k,v in r.items() if k.startswith('image_')},'observed_first_rgba':list(struct.unpack('<4f',data[:16])),'candidate_comparisons':comparisons,'padding_tail_alpha_independently_exact':True,'predeclared_pattern_supported':any(x['mismatch_bytes']==0 for x in comparisons)})
for mode in range(2):
 for route in range(2):need((p/'owned-documents'/('mode%d-phase0-route%d.raw'%(mode,route))).read_bytes()==(p/'owned-documents'/('mode%d-phase2-route%d.raw'%(mode,route))).read_bytes())
v={'status':'predeclared_gray_byte_expectations_falsified','patterns_supported':sum(x['predeclared_pattern_supported'] for x in out),'patterns_rejected':sum(not x['predeclared_pattern_supported'] for x in out),'full_bytes_compared':49152,'padding_bytes_independently_exact':1728,'tail_bytes_independently_exact':18048,'phase0_phase2_bytes_restored':True,'rows':out,'accepted_as_native_goldens':False,'expectations_relaxed':False,'native_repeated':False}
if '--verify-only' in sys.argv:need(parsed((p/'falsification.json').read_text())==v)
else:(p/'falsification.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({k:v[k] for k in v if k!='rows'}))
