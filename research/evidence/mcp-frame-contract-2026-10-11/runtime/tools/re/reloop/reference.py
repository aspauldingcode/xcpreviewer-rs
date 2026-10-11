"""Separate native ImageRenderer A/A and A/B oracle; never Canvas capture."""
from PIL import Image
from reloop.core import ROOT,atomic,digest
from reloop.trace import run
from reloop.verification import bytes_equal


def corpus(out):
    target=out/'reference-capture'
    run(['xcrun','swiftc','-parse-as-library','-module-cache-path',out/'swift-cache',ROOT/'tools/re/fixtures/Reference.swift','-o',target],out,'compile')
    images=[];pixels=[];metadata=[]
    for index,variant in enumerate((0,0,1)):
        path=out/('reference-%d.png'%index)
        run([target,path,str(variant)],out,'capture-%d'%index)
        with Image.open(path) as image:
            image.load();size=image.size;raw=image.convert('RGBA').tobytes()
            metadata.append({'variant':variant,'size':size,'mode':image.mode,'png_sha256':digest(path),'icc_profile_present':bool(image.info.get('icc_profile'))})
        images.append(path);pixels.append(raw);(out/('pixels-%d.rgba'%index)).write_bytes(raw)
    aa=bytes_equal(images[0],images[1]);atomic(out/'repeat-png-comparison.json',aa)
    atomic(out/'repeat-pixel-comparison.json',bytes_equal(out/'pixels-0.rgba',out/'pixels-1.rgba'))
    atomic(out/'changed-pixel-comparison.json',bytes_equal(out/'pixels-0.rgba',out/'pixels-2.rgba'))
    changed=sum(pixels[0][i:i+4]!=pixels[2][i:i+4] for i in range(0,min(len(pixels[0]),len(pixels[2])),4))
    atomic(out/'reference-metadata.json',{'images':metadata,'appearance':'Aqua','scale':1,'reference_source_sha256':digest(ROOT/'tools/re/fixtures/Reference.swift')})
    return {'captures':3,'geometry_matches':all(m['size']==(320,160) for m in metadata),'repeat_pixels_equal':pixels[0]==pixels[1],
            'repeat_png_bytes_equal':aa['passed'],'controlled_changed_pixels':changed,'positive_change_visible':changed>0,
            'scope':'Owned SwiftUI ImageRenderer; fixed 320x160, scale 1, Aqua; same-source fresh-process A/A and one changed text A/B. Not live Xcode Canvas or correlated IPC.'}


def solid_corpus(out):
    """Independent full decoded-frame expectations for explicit owned sRGB literals."""
    import subprocess
    source=ROOT/'tools/re/fixtures/SolidReference.swift';target=out/'solid-reference'
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),
                        str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    comparisons=[];paths=[];metadata=[]
    for ordinal,variant in enumerate((2,2,3)):
        path=out/('solid-%d.png'%ordinal)
        subprocess.run([str(target),str(path),str(variant)],capture_output=True,check=True,timeout=15)
        with Image.open(path) as image:
            size=image.size;raw=image.convert('RGBA').tobytes()
            metadata.append({'variant':variant,'size':list(size),'icc_profile_present':bool(image.info.get('icc_profile'))})
        actual=out/('actual-%d.rgba'%ordinal);actual.write_bytes(raw)
        expected=out/('expected-%d.rgba'%ordinal)
        expected.write_bytes(bytes((255,0,0,255) if variant==2 else (0,0,255,255))*320*160)
        comparison=bytes_equal(expected,actual);comparison['geometry_matches']=size==(320,160)
        comparisons.append(comparison);paths.append(path)
    repeat=bytes_equal(paths[0],paths[1]);atomic(out/'solid-comparisons.json',comparisons)
    atomic(out/'solid-metadata.json',{'images':metadata,'source_sha256':digest(source),'appearance':'Aqua','scale':1})
    atomic(out/'repeat-png-comparison.json',repeat)
    return {'captures':3,'all_expected_rgba':all(c['passed'] and c['geometry_matches'] for c in comparisons),
            'repeat_png_bytes_equal':repeat['passed'],'compared_rgba_bytes':sum(c['reference_bytes'] for c in comparisons),
            'scope':'Separate owned ImageRenderer, 320x160 scale1 Aqua. Entire decoded RGBA including alpha compared to independent color literals; no PNG encoding oracle, row padding, Canvas or IPC claim.'}
