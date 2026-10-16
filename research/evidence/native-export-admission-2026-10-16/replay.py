"""Replay frozen native responses; never launch Xcode or read tool-supplied paths."""
import hashlib
import json
from pathlib import Path
from export_response import normalize,admit_frozen_sentinel,Rejected

def main():
    root=Path(__file__).parent
    pins=json.loads((root/'inputs-seal.json').read_text())
    for name,digest in pins['files'].items():
        if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen input identity changed: '+name)
    native=json.loads((root/'native-results.json').read_text())
    expected=json.loads((root/'expected.json').read_text());rows=[]
    for case in ['sentinel_light','sentinel_dark','sentinel_recovered_light']:
        try:
            if case not in expected:
                normalize(native[case]);raise RuntimeError('Retained failure unexpectedly normalized')
            mapping=expected[case]
            if Path(mapping['local_image']).name!=mapping['local_image']:
                raise ValueError('Invalid frozen local image name')
            result=admit_frozen_sentinel(native[case],(root/mapping['local_image']).read_bytes(),mapping)
            rows.append({'case':case,**result})
        except Rejected as error:
            if case in expected:raise
            rows.append({'case':case,'status':'native_failure_retained','reason':str(error)})
    output={'scope':'Frozen research consumer replay; no native execution','rows':rows,
            'repeatability_accepted':False,'live_provenance':False}
    (root/'replay-result.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output))
if __name__=='__main__':main()
