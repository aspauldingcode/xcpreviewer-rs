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
