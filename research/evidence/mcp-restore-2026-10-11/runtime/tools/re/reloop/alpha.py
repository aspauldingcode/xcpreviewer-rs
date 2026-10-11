"""Independent byte predictions for a bounded native nonlinear sRGB oracle."""
import subprocess
from PIL import Image
from reloop.core import ROOT, atomic, digest
from reloop.verification import bytes_equal

# Declared before execution: straight RGBA export, nearest 8-bit quantization,
# encoded-space source-over opaque blue. Revised competing model quantizes source
# alpha before compositing: blue = 255 - red. Eighth/three-quarter are holdouts.
# Original symmetric half rounding prediction remains in the failed sealed run.
PREDICTIONS = ((0, 0, 0, 0), (255, 0, 0, 64), (255, 0, 0, 128),
               (255, 0, 0, 255), (64, 0, 191, 255), (128, 0, 127, 255),
               (32, 0, 223, 255), (191, 0, 64, 255))


def expected(variant):
    if type(variant) is not int or not 0 <= variant < len(PREDICTIONS):
        raise ValueError('unsupported alpha case')
    return bytes(PREDICTIONS[variant]) * 17 * 9


def corpus(out):
    source = ROOT/'tools/re/fixtures/AlphaReference.swift'
    target = out/'alpha-reference'
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-module-cache-path',
                        str(out/'swift-cache'), str(source), '-o', str(target)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
    atomic(out/'predictions.json', {'rgba': PREDICTIONS, 'size': [17, 9],
                                 'mode': 'nonLinear', 'source_sha256': digest(source)})
    comparisons = []; repeats = []; metadata = []
    for variant in range(8):
        paths = []
        for repeat in range(2):
            name = '%d-%d' % (variant, repeat)
            png = out/('alpha-'+name+'.png')
            subprocess.run([str(target), str(png), str(variant)],
                           capture_output=True, check=True, timeout=10)
            with Image.open(png) as image:
                raw = image.convert('RGBA').tobytes(); size = image.size
                metadata.append({'case': variant, 'repeat': repeat,
                                 'size': size, 'mode': image.mode,
                                 'unique_rgba': sorted(set(tuple(raw[i:i+4]) for i in range(0,len(raw),4))),
                                 'icc_profile_present': bool(image.info.get('icc_profile'))})
            actual = out/('actual-'+name+'.rgba'); actual.write_bytes(raw)
            prediction = out/('expected-'+name+'.rgba'); prediction.write_bytes(expected(variant))
            comparison = bytes_equal(prediction, actual)
            comparison['geometry_matches'] = size == (17, 9)
            comparison['case'] = variant; comparisons.append(comparison); paths.append(actual)
        repeats.append(bytes_equal(*paths))
    atomic(out/'comparisons.json', comparisons); atomic(out/'metadata.json', metadata)
    atomic(out/'repeats.json', repeats)
    return {'captures': 16, 'expected_cases': sum(c['passed'] and c['geometry_matches'] for c in comparisons),
            'repeat_equal_cases': sum(c['passed'] for c in repeats),
            'compared_rgba_bytes': sum(c['reference_bytes'] for c in comparisons),
            'scope': 'Owned 17x9 ImageRenderer nonlinear sRGB straight PNG RGBA; predictions include alpha0, quarter, half, opaque and red over blue. No encoded PNG, padding, Canvas transport or arbitrary color contract.'}
