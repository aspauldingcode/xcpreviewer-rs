"""Independent owned CGContext producer versus pinned ImageRenderer measurements."""
import math
import struct
import subprocess
from fractions import Fraction
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.mixedalpha import CASES, EXTRA_CASES, quantize
from reloop.mixedboundary import layout
from reloop.verification import bytes_equal

RUN='20261010T180037Z-native-mixed-alpha-export-boundary-ab65f9f9'
ANCHOR='1e4eba98fc4be9d17f142476c503ac78d3eb0ec645b00a10a4ec93c3255174d5'
MODELS=('rational-half-up','rational-even','f32-components-double-product','f32-product-half-up','f32-product-even')


def f32(v): return struct.unpack('<f',struct.pack('<f',v))[0]


def prediction(case, model):
    if type(case) is not int or not 0<=case<14 or model not in MODELS: raise ValueError('Unsupported Quartz prediction')
    rgb,n=(CASES+EXTRA_CASES)[case];a=Fraction(n,8);alpha=quantize(a*255)
    if model.startswith('rational'):
        q=round if model=='rational-even' else quantize
        channels=[q(c*a) for c in rgb]
    else:
        components=[f32(c/255) for c in rgb]
        if model=='f32-components-double-product': channels=[math.floor(c*float(a)*255+.5) for c in components]
        else:
            q=round if model=='f32-product-even' else lambda v:math.floor(v+.5)
            channels=[q(f32(f32(c*float(a))*255)) for c in components]
    return (bytes((*channels,alpha))*17+bytes([0xa5])*12)*9


def native_expected(raw):
    if len(raw)!=612: raise ValueError('Unexpected pinned native extent')
    return b''.join(raw[r*68:(r+1)*68]+bytes([0xa5])*12 for r in range(9))


def inspect_metadata(meta,raw):
    stride,order=layout(meta,raw)
    if stride!=80 or order!=(0,1,2,3) or meta['bitmap_info']!=0x4001:
        raise ValueError('Unexpected explicit owned Quartz layout')
    components=meta.get('components')
    if not isinstance(components,list) or len(components)!=4 or any(type(c) not in (int,float) or not math.isfinite(c) or not 0<=c<=1 for c in components):
        raise ValueError('Invalid source component observations')


def corpus(out, public_control=False, normal_control=False):
    public_control=public_control or normal_control
    variants=4 if public_control else 2
    controller=Controller(root=PROJECT_ROOT);v=controller.verify(RUN,ANCHOR)
    if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Native boundary anchor changed')
    source=ROOT/('tools/re/fixtures/MixedAlphaNormalQuartzReference.swift' if normal_control else ('tools/re/fixtures/MixedAlphaPublicQuartzReference.swift' if public_control else 'tools/re/fixtures/MixedAlphaQuartzReference.swift'));target=out/'quartz-contrast'
    atomic(out/'predictions.json',{'models':MODELS,'cases':CASES+EXTRA_CASES,'source_sha256':digest(source),
        'blend_mode':'normal' if normal_control else 'copy','native_run':RUN,'native_anchor':ANCHOR,'padding':165,'inputs':['original Double','public NSColor sRGB']+(['Color.cgColor','NSColor.cgColor'] if public_control else []),
        'scope':'Independent producer contrast; native-derived expectations are relational, rational/float models independent.'})
    for case in range(14):
        for m in MODELS:(out/('expected-%d-%s.raw'%(case,m))).write_bytes(prediction(case,m))
        (out/('native-%d.raw'%case)).write_bytes(native_expected((controller.runs/RUN/'output'/('boundary-%d-0.png.cg.raw'%case)).read_bytes()))
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    rows=[];repeats=[];metadata=[]
    for case in (9,8,*range(8),*range(10,14)):
        paths=[]
        for repeat in range(2):
            prefix=out/('quartz-%d-%d'%(case,repeat))
            subprocess.run([str(target),str(prefix),str(case)],capture_output=True,check=True,timeout=10)
            pair=[]
            for variant in range(variants):
                actual=out/(prefix.name+'.%d.raw'%variant);raw=actual.read_bytes();meta=load(out/(prefix.name+'.%d.json'%variant));inspect_metadata(meta,raw)
                metadata.append({'case':case,'repeat':repeat,'input':variant,**meta});pair.append(actual)
                models={m:bytes_equal(out/('expected-%d-%s.raw'%(case,m)),actual) for m in MODELS}
                if case==9 and not all(c['passed'] for c in models.values()):raise ValueError('Opaque independent Quartz control failed')
                rows.append({'case':case,'repeat':repeat,'input':variant,'models':models,
                    'native':bytes_equal(out/('native-%d.raw'%case),actual),
                    'bridge':bytes_equal(out/(prefix.name+'.1.raw'),actual),
                    'padding_unchanged':all(raw[r*80+68:(r+1)*80]==bytes([0xa5])*12 for r in range(9))})
            paths.append(pair)
        repeats.extend(bytes_equal(paths[0][i],paths[1][i]) for i in range(variants))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'metadata.json',metadata)
    return {'allocations':len(rows),'allocation_bytes':sum(r['native']['candidate_bytes'] for r in rows),
        'padding_bytes':len(rows)*108,'all_padding_unchanged':all(r['padding_unchanged'] for r in rows),
        'repeat_equal_pairs':sum(r['passed'] for r in repeats),
        'public_inputs_equal':all(r['bridge']['passed'] for r in rows if r['input']>=2) if public_control else None,
        'double_bridge_different_cases':len({r['case'] for r in rows if r['input']==0 and not r['bridge']['passed']}),
        'model_matches':{str(i):{m:sum(r['models'][m]['passed'] for r in rows if r['input']==i) for m in MODELS} for i in range(variants)},
        'native_matches':{str(i):sum(r['native']['passed'] for r in rows if r['input']==i) for i in range(variants)},
        'scope':'Owned CGContext source-versus-public-bridge producer contrast with full allocation/padding; independent model matches and pinned ImageRenderer relations distinguished. No general mixed-color or Canvas protocol acceptance.'}

BLEND_RUNS=(('20261010T180803Z-native-mixed-alpha-public-quartz-contrast-35375162','8a02e4157a202765c607119e225d40ad5b4652ffba1a78a7b31b7b777f71f42a'),
            ('20261010T180922Z-native-mixed-alpha-normal-quartz-contrast-2c5d86d7','9f64ffa2a42419af5469cfd67c746d503f30ef76d05a03943d94965bf6f02b32'))


def blend_contrast(out):
    controller=Controller(root=PROJECT_ROOT)
    for rid,anchor in BLEND_RUNS:
        v=controller.verify(rid,anchor)
        if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Blend contrast anchor changed')
    atomic(out/'anchors.json',{'runs':BLEND_RUNS,'comparison':'Every owned raw allocation byte; no pixel normalization'})
    rows=[]
    for case in range(14):
        for repeat in range(2):
            for variant in range(4):
                name='quartz-%d-%d.%d.raw'%(case,repeat,variant)
                rows.append({'case':case,'repeat':repeat,'input':variant,
                    **bytes_equal(controller.runs/BLEND_RUNS[0][0]/'output'/name,controller.runs/BLEND_RUNS[1][0]/'output'/name)})
    atomic(out/'comparisons.json',rows)
    return {'pairs':len(rows),'all_equal':all(r['passed'] for r in rows),
            'compared_bytes':sum(r['reference_bytes'] for r in rows),
            'scope':'Full byte contrast of externally anchored owned copy versus normal CGContext draws over zero active pixels and sentinel padding; no effect here. Not a general blend-mode or ImageRenderer implementation claim.'}
