"""Predeclared competing predictions at an owned mixed-color PNG export boundary."""
from fractions import Fraction
import subprocess
from PIL import Image
from reloop.core import ROOT, atomic, digest
from reloop.verification import bytes_equal

CASES = (((128,64,192),4), ((17,83,201),2), ((1,7,13),1), ((51,153,230),6),
         ((29,113,241),3), ((3,127,253),7), ((89,167,211),5), ((11,73,199),1),
         ((17,83,201),0), ((17,83,201),8))
EXTRA_CASES = (((5,9,13),4), ((7,11,15),4), ((4,12,20),3), ((4,12,20),7))
EVEN_MODEL = 'premultiply-even-exact-alpha'
MODELS = ('straight', 'premultiply-exact-alpha', 'premultiply-quantized-alpha')


def quantize(x):
    return (2*x.numerator+x.denominator)//(2*x.denominator)


def pixel(variant, model):
    if type(variant) is not int or not 0 <= variant < len(CASES+EXTRA_CASES) or model not in (*MODELS,EVEN_MODEL):
        raise ValueError('unsupported mixed alpha prediction')
    rgb, eighths = (CASES+EXTRA_CASES)[variant]; a = Fraction(eighths,8); alpha = quantize(255*a)
    if not alpha:
        return bytes(4)
    if model == 'straight':
        channels = rgb
    else:
        factor = a if model in ('premultiply-exact-alpha',EVEN_MODEL) else Fraction(alpha,255)
        premultiply = round if model == EVEN_MODEL else quantize
        channels = tuple(min(255,quantize(Fraction(premultiply(c*factor)*255,alpha))) for c in rgb)
    return bytes((*channels,alpha))


def compare(out, variant, actual, models=MODELS):
    # No matching/normalizing of actual channels or observed-data fitting.
    result = {}
    for model in models:
        prediction = out/('expected-%d-%s.rgba' % (variant,model))
        result[model] = bytes_equal(prediction,actual)
    return result


def corpus(out, even_control=False):
    cases = CASES+EXTRA_CASES if even_control else CASES
    models = (*MODELS,EVEN_MODEL) if even_control else MODELS
    source = ROOT/('tools/re/fixtures/MixedAlphaEvenReference.swift' if even_control else 'tools/re/fixtures/MixedAlphaReference.swift'); target = out/'mixed-alpha-reference'
    # Freeze complete independent predictions before compilation or first observation.
    predictions = {model:[list(pixel(i,model)) for i in range(len(cases))] for model in models}
    atomic(out/'predictions.json', {'cases': cases, 'models': predictions,
           'discovery_cases': [0,1,2,3], 'holdouts': [4,5,6,7], 'endpoints': [8,9], 'new_even_holdouts': [10,11,12,13] if even_control else [],
           'source_sha256': digest(source), 'size': [17,9], 'mode': 'nonLinear'})
    for model in models:
        for i in range(len(cases)):
            (out/('expected-%d-%s.rgba' % (i,model))).write_bytes(pixel(i,model)*153)
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',
                        str(out/'swift-cache'),str(source),'-o',str(target)],
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    comparisons=[]; repeats=[]; metadata=[]
    for variant in range(len(cases)):
        paths=[]
        for repeat in range(2):
            png=out/('mixed-%d-%d.png' % (variant,repeat))
            subprocess.run([str(target),str(png),str(variant)],capture_output=True,check=True,timeout=10)
            with Image.open(png) as image:
                if image.mode != 'RGBA' or image.size != (17,9):
                    raise ValueError('Unexpected native RGBA geometry/mode')
                raw=image.tobytes()
                metadata.append({'case':variant,'repeat':repeat,'size':image.size,'mode':image.mode,
                    'unique_rgba':sorted(set(tuple(raw[i:i+4]) for i in range(0,len(raw),4))),
                    'icc_profile_present':bool(image.info.get('icc_profile'))})
            actual=out/('actual-%d-%d.rgba' % (variant,repeat)); actual.write_bytes(raw); paths.append(actual)
            comparisons.append({'case':variant,'repeat':repeat,'models':compare(out,variant,actual,models)})
        repeats.append(bytes_equal(*paths))
    atomic(out/'comparisons.json',comparisons); atomic(out/'metadata.json',metadata); atomic(out/'repeats.json',repeats)
    counts={model:sum(c['models'][model]['passed'] for c in comparisons) for model in models}
    holdouts={model:sum(c['models'][model]['passed'] for c in comparisons if 4<=c['case']<=7) for model in models}
    return {'captures':len(comparisons),'repeat_equal_cases':sum(c['passed'] for c in repeats),
            'model_matches':counts,'holdout_matches':holdouts,
            'model_compared_bytes':{m:sum(c['models'][m]['reference_bytes'] for c in comparisons) for m in models},
            'new_even_holdouts_match': all(c['models'][EVEN_MODEL]['passed'] for c in comparisons if c['case']>=10) if even_control else None,
            'models_discriminated':len(set(counts.values()))>1,
            'scope':'Independent competing formulas for owned 17x9 nonlinear sRGB mixed-color straight PNG RGBA export. A supported experiment can falsify models; no general color, native padding or Canvas protocol claim.'}
