"""Owned raw CGImage and two export boundaries; do not fit a general color model."""
from fractions import Fraction
import subprocess
from PIL import Image
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.mixedalpha import CASES, EXTRA_CASES, quantize
from reloop.verification import bytes_equal

MODELS = ('half-up-exact', 'even-exact', 'half-up-quantized')
PRIOR_RUN = '20261010T175037Z-native-mixed-alpha-even-holdouts-cdfa8876'
PRIOR_ANCHOR = '61149f693416489e588210b3b2f1b8a2e226b052e460778915e4167ee2f2117f'


def layout(meta, raw=None):
    for k in ('width','height','bits_per_component','bits_per_pixel','bytes_per_row','bitmap_info','alpha_info','data_bytes'):
        if type(meta.get(k)) is not int:
            raise ValueError('Invalid raw CGImage integer metadata')
    if meta.get('color_space') != 'kCGColorSpaceSRGB':
        raise ValueError('Unsupported raw CGImage color space')
    if (meta['width'],meta['height'],meta['bits_per_component'],meta['bits_per_pixel']) != (17,9,8,32):
        raise ValueError('Unsupported raw CGImage geometry/precision')
    # Explicit endian declarations or the observed default premultiplied-last format.
    # Corpus proves its RGBA mapping with distinct opaque channels before partial alpha.
    info=meta['bitmap_info']; alpha=meta['alpha_info']
    order={ (0,1):(0,1,2,3), (0x2000,2):(2,1,0,3), (0x4000,1):(0,1,2,3),
            (0x2000,1):(3,2,1,0), (0x4000,2):(1,2,3,0)}.get((info&0x7000,alpha))
    if order is None or info&~(0x7000|0x1f) or info&0x1f!=alpha:
        raise ValueError('Unsupported raw CGImage bitmap layout')
    stride=meta['bytes_per_row']
    if not 68<=stride<=4096 or meta['data_bytes']!=stride*9 or (raw is not None and len(raw)!=stride*9):
        raise ValueError('Invalid raw CGImage extent')
    return stride,order


def predicted_raw(case, model, meta):
    if type(case) is not int or not 0<=case<14 or model not in MODELS:
        raise ValueError('Unsupported raw prediction')
    # Layout is measurement metadata; every pixel is independently predicted.
    stride,order=layout(meta)
    rgb,n=(CASES+EXTRA_CASES)[case]; a=Fraction(n,8); alpha=quantize(255*a)
    factor=Fraction(alpha,255) if model=='half-up-quantized' else a
    q=round if model=='even-exact' else quantize
    rgba=(*[q(c*factor) for c in rgb],alpha)
    memory=bytearray(4)
    for channel,index in enumerate(order): memory[index]=rgba[channel]
    # Zero padding is a predeclared falsifiable expectation, not silently skipped.
    return (bytes(memory)*17+bytes(stride-68))*9


def export_prediction(meta, raw):
    stride,order=layout(meta,raw); out=bytearray()
    for row in range(9):
        for col in range(17):
            memory=raw[row*stride+col*4:row*stride+col*4+4]
            r,g,b,a=(memory[i] for i in order)
            out.extend((*[min(255,quantize(Fraction(c*255,a))) if a else 0 for c in (r,g,b)],a))
    return bytes(out)


def decoded(path):
    with Image.open(path) as im:
        if im.size!=(17,9) or im.mode!='RGBA': raise ValueError('Unexpected export geometry/mode')
        return im.tobytes()


def corpus(out):
    controller=Controller(root=PROJECT_ROOT)
    verified=controller.verify(PRIOR_RUN,PRIOR_ANCHOR)
    if not verified.get('valid') or not verified.get('external_anchor_matches'):
        raise ValueError('Prior native measurement anchor changed')
    source=ROOT/'tools/re/fixtures/MixedAlphaBoundaryReference.swift'; target=out/'mixed-boundary'
    atomic(out/'predictions.json',{'cases':CASES+EXTRA_CASES,'raw_models':MODELS,
        'padding':'zero expected; full raw allocation compared',
        'export_relation':'nearest half-up unpremultiply measured CGImage channels using measured alpha; relational, not independent source-pixel oracle',
        'source_sha256':digest(source),'prior_run':PRIOR_RUN,'prior_anchor':PRIOR_ANCHOR})
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    comparisons=[]; repeats=[]; metadata=[]
    for case in (9,8,*range(8),*range(10,14)):
        paths=[]
        for repeat in range(2):
            png=out/('boundary-%d-%d.png'%(case,repeat))
            subprocess.run([str(target),str(png),str(case)],capture_output=True,check=True,timeout=10)
            cg=png.with_name(png.name+'.cg.raw'); meta=load(png.with_name(png.name+'.cg.json')); raw=cg.read_bytes()
            stride,order=layout(meta,raw); metadata.append({'case':case,'repeat':repeat,**meta})
            models={}
            for m in MODELS:
                prediction=out/('expected-%d-%d-%s.raw'%(case,repeat,m)); prediction.write_bytes(predicted_raw(case,m,meta)); models[m]=bytes_equal(prediction,cg)
            if case==9 and not all(c['passed'] for c in models.values()):
                raise ValueError('Owned opaque RGBA mapping control failed')
            legacy=out/('legacy-%d-%d.rgba'%(case,repeat)); legacy.write_bytes(decoded(png))
            direct=out/('direct-%d-%d.rgba'%(case,repeat)); direct.write_bytes(decoded(png.with_name(png.name+'.direct.png')))
            predicted=out/('export-%d-%d.rgba'%(case,repeat)); predicted.write_bytes(export_prediction(meta,raw))
            comparisons.append({'case':case,'repeat':repeat,'raw_models':models,
                'raw_export_relation':bytes_equal(predicted,direct),'legacy_export_relation':bytes_equal(predicted,legacy),
                'direct_legacy':bytes_equal(direct,legacy),
                'prior_native':bytes_equal(controller.runs/PRIOR_RUN/'output'/('actual-%d-0.rgba'%case),legacy),'raw_bytes':len(raw),
                'padding_zero':all(not any(raw[r*stride+68:(r+1)*stride]) for r in range(9))})
            paths.append((cg,direct,legacy))
        repeats.append({name:bytes_equal(paths[0][i],paths[1][i]) for i,name in enumerate(('raw','direct','legacy'))})
    atomic(out/'comparisons.json',comparisons); atomic(out/'metadata.json',metadata); atomic(out/'repeats.json',repeats)
    return {'captures':len(comparisons),'opaque_mapping_controls':sum(c['case']==9 and all(m['passed'] for m in c['raw_models'].values()) for c in comparisons),'all_boundaries_repeat':all(all(c['passed'] for c in r.values()) for r in repeats),
            'raw_model_matches':{m:sum(c['raw_models'][m]['passed'] for c in comparisons) for m in MODELS},
            'raw_bytes':sum(c['raw_bytes'] for c in comparisons),
            'native_padding_bytes':sum(c['raw_bytes']-612 for c in comparisons),'all_padding_zero':all(c['padding_zero'] for c in comparisons),
            'raw_export_matches':sum(c['raw_export_relation']['passed'] for c in comparisons),
            'legacy_export_matches':sum(c['legacy_export_relation']['passed'] for c in comparisons),
            'direct_legacy_matches':sum(c['direct_legacy']['passed'] for c in comparisons),
            'prior_native_matches':sum(c['prior_native']['passed'] for c in comparisons),
            'scope':'Owned mixed-color CGImage provider allocation and two PNG export boundaries. Raw models remain competing; measured-raw export relation is not an independent source oracle or Canvas transport evidence.'}
