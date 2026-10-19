"""Post-acquisition field localization only; no fitted numeric replacement model."""
from pathlib import Path
import json
import compare as c
from acquire import observed
p=Path(__file__).resolve().parent
result=observed(p)
raw=(p/'owned-documents/route0-readback.raw').read_bytes()
identity=c.expected_identity()
old=c.anchored_old(c.parsed((p/'plan.json').read_text())['historical_root'])[0]
fields={}
for label,expected in [('identity',identity),('historical_8bit',old)]:
    counts={'alpha':0,'designated_primary':0,'other_rgb':0}
    for y in range(3):
        for x in range(768):
            for component in range(4):
                offset=y*12352+x*16+component*4
                key='alpha' if component==3 else 'designated_primary' if component==x%3 else 'other_rgb'
                counts[key]+=sum(a!=b for a,b in zip(raw[offset:offset+4],expected[offset:offset+4]))
    fields[label]=counts
print(json.dumps({'comparison':result,'post_acquisition_field_localization':fields,'fitted_model':False,'internal_type_or_order_proven':False,'measured_samples_used_as_goldens':False},sort_keys=True))
