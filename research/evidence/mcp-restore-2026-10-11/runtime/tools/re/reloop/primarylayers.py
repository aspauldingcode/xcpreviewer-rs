"""Independent predeclared source-over predictions for public native layers."""
from fractions import Fraction
import subprocess
from reloop.core import ROOT,PROJECT_ROOT,Controller,atomic,load,digest
from reloop.mixedalpha import quantize
from reloop.mixedcallback import inspect_metadata,target_expected
from reloop.mixedorder import inspect_snapshot
from reloop.verification import bytes_equal

CASES=((0,0,8),(8,0,8),(0,8,8),(0,0,0),(4,2,8),(2,4,8),(1,6,8),(7,3,8),(4,4,4),(3,5,2),(6,1,0),(2,3,6))
EXTRA_CASES=((3,3,8),(5,7,8),(7,5,8),(3,7,3),(5,1,7),(1,7,5),(7,7,1),(3,1,5))
MODELS=('quantized-stage','exact-final','exact-stage')
ANCHORS=(('20261010T183453Z-native-mixed-alpha-rasterization-scale-c9636cdf','e7e59c73057eb4801a306c0e0fb3afe79422b8876fe1e6adeaaf0e7156d65dcd'),('20261010T183552Z-native-mixed-alpha-drawing-group-fea18d4f','80f02e84ec2de13eb02a7ea02534b0150840a08e57032c1e37c50df44120eec9'))


def pixel(case,order,model):
    if type(case) is not int or not 0<=case<len(CASES+EXTRA_CASES) or order not in ('forward','reverse') or model not in MODELS:raise ValueError('Invalid layer prediction')
    result=[Fraction(0)]*4
    for channel in ((2,0,1) if order=='forward' else (1,0,2)):
        alpha=Fraction((CASES+EXTRA_CASES)[case][channel],8)
        if model=='quantized-stage':alpha=Fraction(quantize(alpha*255),255)
        for c in range(4):
            source=alpha if c in (channel,3) else 0
            result[c]=source+result[c]*(1-alpha)
            if model!='exact-final':result[c]=Fraction(quantize(result[c]*255),255)
    return bytes(quantize(v*255) for v in result)


def inspect_layer(meta,raw,index,order):
    inspect_metadata(meta,raw,0)
    if type(index) is not int or not 0<=index<4 or order not in ('forward','reverse'):raise ValueError('Invalid layer target')
    if type(meta.get('target_index')) is not int or meta['target_index']!=index or meta.get('layer_order')!=order:raise ValueError('Invalid layer identity')
    if type(meta.get('drawing_group')) is not bool or meta['drawing_group']!=(index>=2):raise ValueError('Invalid group identity')
    if type(meta.get('rasterization_scale')) not in (int,float) or meta['rasterization_scale']!=(1 if index%2==0 else 2):raise ValueError('Invalid layer scale')


def corpus(out,holdout=False):
    count=20 if holdout else 12
    controller=Controller(root=PROJECT_ROOT)
    for run,anchor in ANCHORS+(('20261010T184512Z-native-primary-layer-composition-c5d47964','010c8a705392ddbe4f14cdea4e0f1f9c555e1bf7f04e494fe0e37eaa4bf5712f'),) if holdout else ANCHORS:
        v=controller.verify(run,anchor)
        if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Layer prerequisite evidence changed')
    source=ROOT/('tools/re/fixtures/PrimaryLayerHoldoutReference.swift' if holdout else 'tools/re/fixtures/PrimaryLayerReference.swift');target=out/'primary-layers'
    atomic(out/'predictions.json',{'cases':(CASES+EXTRA_CASES)[:count],'models':MODELS,'source_sha256':digest(source),'controls':[0,1,2,3],'discovery':[4,5],'holdouts':list(range(6,count)),'new_holdouts':list(range(12,count)),
        'expectations':'quantized-stage rounds source alpha and each premultiplied output to8bits; exact-stage uses exact source eighths then rounds each output; exact-final rounds only after all rational source-over layers. No native observations used.',
        'scope':'Getter and callback full allocations compared independently to source predictions; modifier output equality does not prove offscreen execution.'})
    for case in range(count):
        for order in ('forward','reverse'):
            for m in MODELS:
                raw=pixel(case,order,m)*153
                (out/('expected-%d-%s-%s.cg.raw'%(case,order,m))).write_bytes(raw)
                (out/('expected-%d-%s-%s.raw'%(case,order,m))).write_bytes(target_expected(raw,80))
    with (out/'compile.log').open('wb') as log:subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    rows=[];repeats=[];matrix=[]
    for case in range(count):
        for order in ('forward','reverse'):
            for repeat in range(2):
                prefix='layers-%d-%s-%d'%(case,order,repeat)
                subprocess.run([str(target),str(out/prefix),str(case),order],capture_output=True,check=True,timeout=10)
                for index in range(4):
                    path=out/(prefix+'.%d.raw'%index);raw=path.read_bytes();inspect_layer(load(path.with_suffix('.json')),raw,index,order)
                    cg=out/(prefix+'.%d.cg.raw'%index);cgraw=cg.read_bytes();inspect_snapshot(load(cg.with_suffix('.json')),cgraw)
                    relational=out/(prefix+'.%d.getter-expected.raw'%index);relational.write_bytes(target_expected(cgraw,80))
                    rows.append({'case':case,'order':order,'repeat':repeat,'target':index,'models':{m:{'callback':bytes_equal(out/('expected-%d-%s-%s.raw'%(case,order,m)),path),'getter':bytes_equal(out/('expected-%d-%s-%s.cg.raw'%(case,order,m)),cg)} for m in MODELS},'getter_callback':bytes_equal(relational,path),'padding_unchanged':all(raw[r*80+68:(r+1)*80]==bytes([165])*12 for r in range(9))})
                    if index:matrix.append(bytes_equal(out/(prefix+'.0.raw'),path))
            for index in range(4):
                for suffix in ('raw','cg.raw'):repeats.append(bytes_equal(out/('layers-%d-%s-0.%d.%s'%(case,order,index,suffix)),out/('layers-%d-%s-1.%d.%s'%(case,order,index,suffix))))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'matrix.json',matrix)
    changed=bytes_equal(out/'layers-1-forward-0.0.raw',out/'layers-1-reverse-0.0.raw');atomic(out/'positive-change.json',changed)
    return {'captures':count*4,'allocations':len(rows),'callback_events':len(rows),'callback_bytes':len(rows)*720,'getter_bytes':len(rows)*612,'padding_bytes':len(rows)*108,
        'all_padding_unchanged':all(r['padding_unchanged'] for r in rows),'repeat_equal_pairs':sum(p['passed'] for p in repeats),'matrix_equal_pairs':sum(p['passed'] for p in matrix),'getter_callback_matches':sum(r['getter_callback']['passed'] for r in rows),
        'endpoint_source_matches':sum(r['case']<4 and all(p['callback']['passed'] and p['getter']['passed'] for p in r['models'].values()) for r in rows),'positive_layer_order_change':not changed['passed'],
        'new_holdout_matches':{m:{boundary:sum(r['models'][m][boundary]['passed'] for r in rows if r['case']>=12) for boundary in ('getter','callback')} for m in MODELS},
        'model_matches':{m:{boundary:sum(r['models'][m][boundary]['passed'] for r in rows) for boundary in ('getter','callback')} for m in MODELS},
        'scope':'Owned public primary-layer source-over controls with explicit grouped/ungrouped and scale1/2 targets. Independent rational predictions, native getter/callback relations and padding separate; no Canvas transport or universal compositing model.'}
