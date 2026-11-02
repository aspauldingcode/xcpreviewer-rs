"""Public callback scale and call-order controls, fixed source/target pixels."""
import subprocess
from reloop.core import ROOT,PROJECT_ROOT,Controller,atomic,digest,load
from reloop.mixedcallback import inspect_metadata,target_expected
from reloop.mixedquartz import RUN,ANCHOR,MODELS,prediction
from reloop.mixedorder import ORDER_RUN,ORDER_ANCHOR
from reloop.verification import bytes_equal

SCALES=(1,2,0.5,4)
ORDERS=('forward','reverse')


def inspect_scale(meta,raw,index,order):
    inspect_metadata(meta,raw,0)
    if type(index) is not int or not 0<=index<4 or order not in ORDERS:
        raise ValueError('Invalid scale target identity')
    scale=(SCALES if order=='forward' else SCALES[::-1])[index]
    if type(meta.get('rasterization_scale')) not in (int,float) or meta['rasterization_scale']!=scale:
        raise ValueError('Invalid rasterization scale')
    if type(meta.get('target_index')) is not int or meta['target_index']!=index or meta.get('scale_order')!=order:
        raise ValueError('Invalid scale order identity')


def corpus(out,group_control=False):
    controller=Controller(root=PROJECT_ROOT)
    for run,anchor in ((RUN,ANCHOR),(ORDER_RUN,ORDER_ANCHOR)):
        v=controller.verify(run,anchor)
        if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Native scale evidence anchor changed')
    source=ROOT/('tools/re/fixtures/MixedAlphaGroupReference.swift' if group_control else 'tools/re/fixtures/MixedAlphaScaleReference.swift');target=out/'scale-reference'
    atomic(out/'predictions.json',{'source_sha256':digest(source),'drawing_group':group_control,'scales':SCALES,'orders':ORDERS,
        'getter_run':RUN,'getter_anchor':ANCHOR,'callback_run':ORDER_RUN,'callback_anchor':ORDER_ANCHOR,
        'models':MODELS,'fixed_geometry':[17,9],'stride':80,'padding':165,
        'competing_explanations':['Changing rasterizationScale changes target bytes at fixed geometry.','Scale-order/cache initialization changes equal-scale targets.','All scales preserve callback output and prior getter gap.'],
        'scope':'Explicit scale controls; all full buffers compared. Native-derived relations distinct from independent source models; no Canvas wire.'})
    for case in range(14):
        native=(controller.runs/RUN/'output'/('boundary-%d-0.png.cg.raw'%case)).read_bytes()
        (out/('getter-%d.raw'%case)).write_bytes(target_expected(native,80))
        prior=controller.runs/ORDER_RUN/'output'/('order-%d-cg-first-0.draw0.raw'%case)
        raw=prior.read_bytes();inspect_metadata(load(prior.with_suffix('.json')),raw,0)
        (out/('callback-%d.raw'%case)).write_bytes(raw)
        for m in MODELS:(out/('expected-%d-%s.raw'%(case,m))).write_bytes(prediction(case,m))
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    rows=[];repeats=[];order_pairs=[]
    for case in (9,8,*range(8),*range(10,14)):
        for order in ORDERS:
            for repeat in range(2):
                prefix=out/('scale-%d-%s-%d'%(case,order,repeat))
                subprocess.run([str(target),str(prefix),str(case),order],capture_output=True,check=True,timeout=10)
                for index in range(4):
                    path=out/(prefix.name+'.%d.raw'%index);raw=path.read_bytes();meta=load(path.with_suffix('.json'))
                    inspect_scale(meta,raw,index,order)
                    rows.append({'case':case,'order':order,'repeat':repeat,'scale':meta['rasterization_scale'],
                        'getter':bytes_equal(out/('getter-%d.raw'%case),path),'callback':bytes_equal(out/('callback-%d.raw'%case),path),
                        'models':{m:bytes_equal(out/('expected-%d-%s.raw'%(case,m)),path) for m in MODELS},
                        'padding_unchanged':all(raw[r*80+68:(r+1)*80]==bytes([165])*12 for r in range(9))})
            for index in range(4):repeats.append(bytes_equal(out/('scale-%d-%s-0.%d.raw'%(case,order,index)),out/('scale-%d-%s-1.%d.raw'%(case,order,index))))
        for repeat in range(2):
            for index in range(4):order_pairs.append(bytes_equal(out/('scale-%d-forward-%d.%d.raw'%(case,repeat,index)),out/('scale-%d-reverse-%d.%d.raw'%(case,repeat,3-index))))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'order-pairs.json',order_pairs)
    return {'drawing_group':group_control,'captures':56,'allocations':len(rows),'callback_events':len(rows),'allocation_bytes':len(rows)*720,'padding_bytes':len(rows)*108,
        'repeat_equal_pairs':sum(p['passed'] for p in repeats),'order_equal_pairs':sum(p['passed'] for p in order_pairs),
        'all_padding_unchanged':all(r['padding_unchanged'] for r in rows),
        'opaque_source_matches':sum(r['case']==9 and r['models']['rational-half-up']['passed'] for r in rows),
        'callback_matches':sum(r['callback']['passed'] for r in rows),'getter_matches':sum(r['getter']['passed'] for r in rows),
        'getter_mismatched_cases':sorted(set(r['case'] for r in rows if not r['getter']['passed'])),
        'model_matches':{str(s):{m:sum(r['models'][m]['passed'] for r in rows if r['scale']==s) for m in MODELS} for s in SCALES},
        'scope':'Owned four rasterization scales at fixed source and output with forward/reverse order; complete target/padding comparisons, pinned native relations and separate independent source models. No universal color or Canvas transport claim.'}
