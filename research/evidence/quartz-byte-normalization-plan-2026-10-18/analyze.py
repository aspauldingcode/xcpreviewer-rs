"""Retrospective model discrimination on a previously sealed owned measurement."""
import hashlib,json,sys
from pathlib import Path
from models import domain,predict,RECIPROCAL_BITS
PARENT_SEAL='eafb11df59f30a00c61c406c6698ce98dc7b3da520295b1f280900845d6db9e6'
def analyze(parent):
    parent=Path(parent)
    seal_bytes=(parent/'seal.json').read_bytes()
    if hashlib.sha256(seal_bytes).hexdigest()!=PARENT_SEAL:raise ValueError('parent seal changed')
    seal=json.loads(seal_bytes)
    for name,digest in seal['files'].items():
        p=parent/name
        if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('parent file changed')
    results=[]
    for phase in range(3):
        base=parent/'export/owned-documents'
        source=(base/('mode0-phase%d-provider.raw'%phase)).read_bytes()
        observed=(base/('mode0-phase%d-readback.raw'%phase)).read_bytes()
        if len(source)!=612 or len(observed)!=4096:raise ValueError('geometry')
        mismatches={}
        for model in ['division','reciprocal']:
            expected=bytearray(b'\xa5'*4096)
            for y in range(9):
                for x in range(17):
                    offset=(y*17+x)*4
                    expected[y*288+x*16:y*288+x*16+16]=b''.join(predict(v,model) for v in source[offset:offset+4])
            mismatches[model]=sum(a!=b for a,b in zip(expected,observed))
        results.append({'phase':phase,'allocation_bytes_compared':4096,'model_mismatch_bytes':mismatches})
    table=domain()
    return {'retrospective_only':True,'native_jobs':0,'parent_seal_sha256':PARENT_SEAL,'reciprocal_bits_hex':hex(RECIPROCAL_BITS),'domain_disagreement_bytes':[x['byte'] for x in table if x['division_hex']!=x['reciprocal_hex']],'results':results,'native_cause_proven':False,'prospective_quartz_control_executed':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(analyze(Path(sys.argv[1]))))
