"""Post-acquisition field-localization only; never constructs replacement goldens."""
from pathlib import Path
import json,struct
from admit import observed
from predictions import readback
p=Path(__file__).resolve().parent;result=observed(p);rows=[]
for route in range(3):
 raw=(p/'owned-documents'/('route%d-readback.raw'%route)).read_bytes();expected=readback(route,'iec_srgb' if route==2 else 'alpha_invariant');counts={'alpha_bytes':0,'designated_primary_bytes':0,'other_RGB_bytes':0,'gray_RGB_bytes':0}
 for y in range(3):
  for x in range(768):
   for c in range(4):
    o=y*12352+x*16+c*4;n=sum(a!=b for a,b in zip(raw[o:o+4],expected[o:o+4]));key='alpha_bytes' if c==3 else 'gray_RGB_bytes' if route==2 else 'designated_primary_bytes' if c==x%3 else 'other_RGB_bytes';counts[key]+=n
 samples=[{'column':x,'rgba':list(struct.unpack_from('<4f',raw,x*16))} for x in ([0,3,4,5,384,385,386,765,766,767] if route<2 else [0])]
 rows.append({'route':route,'byte_mismatches_by_field':counts,'observed_samples_diagnostic_only':samples})
result['field_localization']=rows;result['numerical_contract_rejected']=True;result['measured_samples_used_as_goldens']=False
print(json.dumps(result))
