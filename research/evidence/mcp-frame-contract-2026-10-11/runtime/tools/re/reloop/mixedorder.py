"""Same-instance public renderer order and retained-provider falsification."""
import subprocess
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.mixedboundary import layout
from reloop.mixedcallback import inspect_metadata, target_expected, active_pixels
from reloop.mixedquartz import RUN, ANCHOR, MODELS, prediction
from reloop.verification import bytes_equal

STAGES=('initial','after-draw','after-second-draw','after-export')
ORDERS=('cg-first','callback-first')


def inspect_snapshot(meta,raw):
    stride,order=layout(meta,raw)
    if stride!=68 or order!=(0,1,2,3) or meta['bitmap_info']!=1:
        raise ValueError('Unexpected immediate provider layout')


def corpus(out):
    controller=Controller(root=PROJECT_ROOT)
    verified=controller.verify(RUN,ANCHOR)
    if not verified.get('valid') or not verified.get('external_anchor_matches'):
        raise ValueError('Native order oracle anchor changed')
    source=ROOT/'tools/re/fixtures/MixedAlphaOrderReference.swift';target=out/'order-reference'
    atomic(out/'predictions.json',{'source_sha256':digest(source),'native_run':RUN,'native_anchor':ANCHOR,
        'orders':ORDERS,'stages':STAGES,'source_models':MODELS,
        'competing_explanations':['Original retained provider changes after subsequent operations; or getter pixels depend on call order.',
            'Immediate cgImage bytes stay stable and differ from draw callback regardless of order.'],
        'scope':'Force independent immediate CFData copies; compare every provider byte and every padded callback allocation; no source model promoted by native-derived equality.'})
    for case in range(14):
        native=(controller.runs/RUN/'output'/('boundary-%d-0.png.cg.raw'%case)).read_bytes()
        if len(native)!=612:raise ValueError('Native order anchor extent changed')
        (out/('native-%d.raw'%case)).write_bytes(native)
        for model in MODELS:(out/('expected-%d-%s.raw'%(case,model))).write_bytes(prediction(case,model))
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    rows=[];repeats=[];order_pairs=[];padding=[];opaque=0
    for case in (9,8,*range(8),*range(10,14)):
        for order in ORDERS:
            for repeat in range(2):
                prefix=out/('order-%d-%s-%d'%(case,order,repeat))
                subprocess.run([str(target),str(prefix),str(case),order],capture_output=True,check=True,timeout=10)
                initial=out/(prefix.name+'.initial.raw')
                getters=[];retained=[];draws=[];models=[]
                for stage in STAGES:
                    path=out/(prefix.name+'.'+stage+'.raw');raw=path.read_bytes()
                    inspect_snapshot(load(out/(prefix.name+'.'+stage+'.json')),raw)
                    getters.append({'stage':stage,'initial':bytes_equal(initial,path),'native_anchor':bytes_equal(out/('native-%d.raw'%case),path)})
                    deferred=out/(prefix.name+'.'+stage+'.retained.raw')
                    retained.append({'stage':stage,'comparison':bytes_equal(initial,deferred)})
                for stage in ('draw0','draw1'):
                    path=out/(prefix.name+'.'+stage+'.raw');raw=path.read_bytes()
                    inspect_metadata(load(out/(prefix.name+'.'+stage+'.json')),raw,0)
                    padding.append(all(raw[r*80+68:(r+1)*80]==bytes([165])*12 for r in range(9)))
                    expected=out/(prefix.name+'.'+stage+'.native-expected.raw')
                    expected.write_bytes(target_expected(initial.read_bytes(),80))
                    draws.append({'stage':stage,'getter_relation':bytes_equal(expected,path)})
                    model={m:bytes_equal(out/('expected-%d-%s.raw'%(case,m)),path) for m in MODELS};models.append(model)
                    if case==9 and model['rational-half-up']['passed']:opaque+=1
                row={'case':case,'order':order,'repeat':repeat,'getters':getters,'retained':retained,'draws':draws,'source_models':models}
                rows.append(row)
            for stage in (*STAGES,'draw0','draw1'):
                repeats.append(bytes_equal(out/('order-%d-%s-0.%s.raw'%(case,order,stage)),out/('order-%d-%s-1.%s.raw'%(case,order,stage))))
        for repeat in range(2):
            for stage in (*STAGES,'draw0','draw1'):
                order_pairs.append(bytes_equal(out/('order-%d-cg-first-%d.%s.raw'%(case,repeat,stage)),out/('order-%d-callback-first-%d.%s.raw'%(case,repeat,stage))))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'order-pairs.json',order_pairs)
    return {'captures':len(rows),'callback_events':len(rows)*2,'provider_snapshot_bytes':len(rows)*8*612,
        'callback_allocation_bytes':len(rows)*2*720,'padding_bytes':len(rows)*2*108,
        'repeat_equal_pairs':sum(p['passed'] for p in repeats),'order_equal_pairs':sum(p['passed'] for p in order_pairs),
        'all_padding_unchanged':all(padding),'opaque_source_matches':opaque,
        'all_getters_stable':all(g['initial']['passed'] for row in rows for g in row['getters']),
        'all_retained_stable':all(g['comparison']['passed'] for row in rows for g in row['retained']),
        'native_anchor_matches':sum(g['native_anchor']['passed'] for row in rows for g in row['getters']),
        'callback_getter_matches':sum(g['getter_relation']['passed'] for row in rows for g in row['draws']),
        'mismatched_cases':sorted(set(row['case'] for row in rows if any(not d['getter_relation']['passed'] for d in row['draws']))),
        'scope':'Owned same-instance immediate copies versus retained providers, changed call order, public callback targets and nsImage export. Native reference relation separate from independent source predictions; no Canvas protocol or universal color model.'}

ORDER_RUN='20261010T182739Z-native-mixed-alpha-render-order-9d110f33'
# External anchor assigned after the complete acquisition manifest was verified.
ORDER_ANCHOR='195b54b87dc547bcc0a5d187f0b454f53ab946f7dce0813ee6bfab2b0765f236'


def export_contrast(out):
    from reloop.mixedboundary import decoded,export_prediction
    controller=Controller(root=PROJECT_ROOT);verified=controller.verify(ORDER_RUN,ORDER_ANCHOR)
    if not verified.get('valid') or not verified.get('external_anchor_matches'):
        raise ValueError('Same-instance order evidence anchor changed')
    source=controller.runs/ORDER_RUN/'output';rows=[];repeats=[];orders=[]
    atomic(out/'predictions.json',{'source_run':ORDER_RUN,'source_anchor':ORDER_ANCHOR,
        'relation':'Each immediately copied provider predicts its same-instance nsImage PNG via declared integer half-up unpremultiplication; compare all decoded RGBA bytes. No independent source-pixel oracle.',
        'padding':'All 112 complete callback targets retain separately checked a5 padding; no pixel fitting.'})
    for case in range(14):
        for order in ORDERS:
            for repeat in range(2):
                prefix='order-%d-%s-%d'%(case,order,repeat)
                actual=out/(prefix+'.export.rgba');actual.write_bytes(decoded(source/(prefix+'.export.png')))
                relations=[]
                for stage in STAGES:
                    raw=(source/(prefix+'.'+stage+'.raw')).read_bytes();meta=load(source/(prefix+'.'+stage+'.json'))
                    inspect_snapshot(meta,raw)
                    predicted=out/(prefix+'.'+stage+'.predicted.rgba');predicted.write_bytes(export_prediction(meta,raw))
                    relations.append(bytes_equal(predicted,actual))
                rows.append({'case':case,'order':order,'repeat':repeat,'provider_export_relations':relations})
            repeats.append(bytes_equal(out/('order-%d-%s-0.export.rgba'%(case,order)),out/('order-%d-%s-1.export.rgba'%(case,order))))
        for repeat in range(2):orders.append(bytes_equal(out/('order-%d-cg-first-%d.export.rgba'%(case,repeat)),out/('order-%d-callback-first-%d.export.rgba'%(case,repeat))))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'orders.json',orders)
    return {'exports':56,'decoded_rgba_bytes':56*612,'provider_export_matches':sum(p['passed'] for r in rows for p in r['provider_export_relations']),
        'repeat_equal_pairs':sum(p['passed'] for p in repeats),'order_equal_pairs':sum(p['passed'] for p in orders),
        'scope':'Reused sealed native captures; full decoded export pixels compared to declared immediate-provider relation, repeat and call order. No additional acquisition or PNG container identity claim.'}
