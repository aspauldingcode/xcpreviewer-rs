"""Public native callback extent holdouts, full allocation/padding/tail predictions."""
import subprocess
from reloop.core import Controller,ROOT,PROJECT_ROOT,atomic,load,digest
from reloop.primarysource import parse,expression,expected
from reloop.browsersource import RUN,ANCHOR
from reloop.verification import bytes_equal

CASES=(4,8,18,19)
EXTENTS=((1,1,4),(1,1,16),(13,7,52),(13,7,64),(64,64,256))


def corpus(out):
    verification=Controller(root=PROJECT_ROOT).verify(RUN,ANCHOR)
    if not verification['valid'] or not verification['external_anchor_matches']:raise ValueError('Source prerequisite anchor changed')
    atomic(out/'source-anchor.json',verification)
    source=ROOT/'tools/re/fixtures/PrimaryExtentReference.swift';target=out/'extent-reference'
    jobs=[]
    for case in CASES:
        for reverse in (0,1):
            for width,height,stride in EXTENTS:
                config=parse(expression(case,reverse,width,height));i=len(jobs)
                (out/('expected-%d.raw'%i)).write_bytes(expected(config,stride))
                jobs.append({'index':i,'case':case,'order':'reverse' if reverse else 'forward','config':config,'stride':stride})
    atomic(out/'predictions.json',{'jobs':jobs,'source_sha256':digest(source),'scope':'Public native ImageRenderer callback scale1 ungrouped explicit sRGB premultiplied RGBA target. Independent Fraction model fixed before native execution; full16384 bytes including declared A5 row padding/C3 unused tail. No getter/PNG/Canvas transport claim.'})
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    comparisons=[];repeats=[];metadata=[]
    for job in jobs:
        i=job['index'];c=job['config'];stride=job['stride']
        for repeat in range(2):
            prefix=out/('native-%d-%d'%(i,repeat))
            r=subprocess.run([str(target),str(prefix),str(job['case']),str(c['width']),str(c['height']),str(stride),job['order']],capture_output=True,timeout=10)
            prefix.with_suffix('.stdout').write_bytes(r.stdout);prefix.with_suffix('.stderr').write_bytes(r.stderr)
            if r.returncode:raise ValueError('Owned native extent reference failed')
            m=load(prefix.with_suffix('.json'))
            exact={'width':c['width'],'height':c['height'],'stride':stride,'case':job['case'],'order':job['order'],'callback_count':1,'allocation_bytes':16384,'bitmap_info':16385,'alpha_info':1,'bits_per_component':8,'bits_per_pixel':32,'color_space':'kCGColorSpaceSRGB','rasterization_scale':1,'drawing_group':False,'reported_size':[c['width'],c['height']]}
            if set(m)!=set(exact) or any(m[k]!=v or (k not in ('reported_size',) and type(m[k]) is not type(v)) for k,v in exact.items()):raise ValueError('Native extent metadata contract mismatch')
            metadata.append(m);comparisons.append(bytes_equal(out/('expected-%d.raw'%i),prefix.with_suffix('.raw')))
        repeats.append(bytes_equal(out/('native-%d-0.raw'%i),out/('native-%d-1.raw'%i)))
    atomic(out/'comparisons.json',comparisons);atomic(out/'repeats.json',repeats);atomic(out/'metadata.json',metadata)
    return {'jobs':len(jobs),'captures':len(comparisons),'full_allocation_bytes':len(comparisons)*16384,'independent_matches':sum(r['passed'] for r in comparisons),'repeat_pairs':len(repeats),'repeat_matches':sum(r['passed'] for r in repeats),'padding_bytes':sum((j['stride']-j['config']['width']*4)*j['config']['height']*2 for j in jobs),'tail_bytes':sum((16384-j['stride']*j['config']['height'])*2 for j in jobs),'scope':'Independent public native extent oracle only. Four primary-alpha cases, two orders, five compact/padded 1x1/13x7/64x64 targets, scale1 ungrouped. Full target padding/tail included. No arbitrary size, native getter/PNG, Canvas protocol or portable delivery acceptance.'}
