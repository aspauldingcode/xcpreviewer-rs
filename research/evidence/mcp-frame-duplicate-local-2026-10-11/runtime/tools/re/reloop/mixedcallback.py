"""Owned public ImageRenderer callback into an explicit padded CGContext."""
import subprocess
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.mixedboundary import layout
from reloop.mixedquartz import RUN, ANCHOR, MODELS, prediction
from reloop.verification import bytes_equal


LAYOUTS=((68,1),(80,1),(68,0x4001),(80,0x4001))


def inspect_metadata(meta,raw,variant,layout_control=False):
    stride,order=layout(meta,raw)
    variants=4 if layout_control else 2
    if type(variant) is not int or not 0<=variant<variants:raise ValueError('Invalid callback target index')
    expected_stride,expected_info=LAYOUTS[variant] if layout_control else (80,0x4001)
    if stride!=expected_stride or order!=(0,1,2,3) or meta['bitmap_info']!=expected_info:
        raise ValueError('Unexpected callback target layout')
    if type(meta.get('callback_count')) is not int or meta['callback_count']!=1:
        raise ValueError('Invalid callback event accounting')
    size=meta.get('reported_size')
    if not isinstance(size,list) or len(size)!=2 or any(type(v) not in (int,float) for v in size) or size!=[17,9]:
        raise ValueError('Unexpected callback geometry')
    if layout_control and any(type(meta.get(k)) is not int or meta[k]!=v for k,v in [('target_index',variant),('requested_stride',expected_stride),('requested_bitmap_info',expected_info)]):raise ValueError('Invalid callback layout request identity')
    if meta.get('blend_mode')!=('normal' if layout_control else ('normal','copy')[variant]):raise ValueError('Unexpected callback blend state')


def target_expected(raw,stride):
    if len(raw)!=612 or type(stride) is not int or stride not in (68,80):raise ValueError('Unsupported callback expected extent')
    return b''.join(raw[r*68:(r+1)*68]+bytes([0xa5])*(stride-68) for r in range(9))


def active_pixels(raw,stride):
    if type(stride) is not int or stride not in (68,80) or len(raw)!=stride*9:raise ValueError('Unsupported callback active extent')
    # Exact physical pixel extraction; padding checked separately in full comparisons.
    return b''.join(raw[r*stride:r*stride+68] for r in range(9))


def corpus(out,layout_control=False):
    variants=4 if layout_control else 2
    controller=Controller(root=PROJECT_ROOT);v=controller.verify(RUN,ANCHOR)
    if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Native callback oracle anchor changed')
    source=ROOT/('tools/re/fixtures/MixedAlphaCallbackLayoutReference.swift' if layout_control else 'tools/re/fixtures/MixedAlphaCallbackReference.swift');target=out/'callback-reference'
    atomic(out/'predictions.json',{'native_run':RUN,'native_anchor':ANCHOR,'source_sha256':digest(source),
        'models':MODELS,'size':[17,9],'layouts':LAYOUTS if layout_control else [(80,0x4001),(80,0x4001)],'stride':None if layout_control else 80,'padding':165,'blend_modes':['normal']*4 if layout_control else ['normal','copy'],
        'scope':'Native oracle relation and independent source predictions separate; callback must run exactly once per target.'})
    for case in range(14):
        native=(controller.runs/RUN/'output'/('boundary-%d-0.png.cg.raw'%case)).read_bytes()
        for variant in range(variants):
            stride=LAYOUTS[variant][0] if layout_control else 80
            for m in MODELS:
                padded=prediction(case,m)
                active=b''.join(padded[r*80:r*80+68] for r in range(9))
                (out/('expected-%d-%d-%s.raw'%(case,variant,m))).write_bytes(target_expected(active,stride))
            (out/('native-%d-%d.raw'%(case,variant))).write_bytes(target_expected(native,stride))
    with (out/'compile.log').open('wb') as log:
        subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(out/'swift-cache'),str(source),'-o',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    rows=[];repeats=[];metadata=[]
    for case in (9,8,*range(8),*range(10,14)):
        paths=[]
        for repeat in range(2):
            prefix=out/('callback-%d-%d'%(case,repeat))
            subprocess.run([str(target),str(prefix),str(case)],capture_output=True,check=True,timeout=10)
            pair=[]
            for variant in range(variants):
                actual=out/(prefix.name+'.%d.raw'%variant);raw=actual.read_bytes();meta=load(out/(prefix.name+'.%d.json'%variant));inspect_metadata(meta,raw,variant,layout_control)
                metadata.append({'case':case,'repeat':repeat,'target':variant,**meta});pair.append(actual)
                active=out/(prefix.name+'.%d.active.rgba'%variant);active.write_bytes(active_pixels(raw,meta['bytes_per_row']))
                models={m:bytes_equal(out/('expected-%d-%d-%s.raw'%(case,variant,m)),actual) for m in MODELS}
                rows.append({'case':case,'repeat':repeat,'target':variant,'models':models,
                    'native':bytes_equal(out/('native-%d-%d.raw'%(case,variant)),actual),
                    'target_full_extent':bytes_equal(out/(prefix.name+'.0.raw'),actual),
                    'active_relation':bytes_equal(out/(prefix.name+'.0.active.rgba'),active),
                    'padding_unchanged':all(raw[r*meta['bytes_per_row']+68:(r+1)*meta['bytes_per_row']]==bytes([0xa5])*(meta['bytes_per_row']-68) for r in range(9))})
            paths.append(pair)
        repeats.extend(bytes_equal(paths[0][i],paths[1][i]) for i in range(variants))
    atomic(out/'comparisons.json',rows);atomic(out/'repeats.json',repeats);atomic(out/'metadata.json',metadata)
    return {'allocations':len(rows),'allocation_bytes':sum(r['native']['candidate_bytes'] for r in rows),
        'padding_bytes':sum(r['native']['candidate_bytes']-612 for r in rows),'all_padding_unchanged':all(r['padding_unchanged'] for r in rows),
        'repeat_equal_pairs':sum(r['passed'] for r in repeats), 'callback_events':sum(m['callback_count'] for m in metadata),
        'all_full_target_buffers_equal':all(r['target_full_extent']['passed'] for r in rows),
        'all_active_targets_equal':all(r['active_relation']['passed'] for r in rows if r['target']>0),
        'active_relation_pairs':sum(r['target']>0 for r in rows),
        'active_relation_bytes':sum(r['active_relation']['reference_bytes'] for r in rows if r['target']>0),
        'opaque_source_matches':sum(r['case']==9 and r['models']['rational-half-up']['passed'] for r in rows),
        'model_matches':{str(i):{m:sum(r['models'][m]['passed'] for r in rows if r['target']==i) for m in MODELS} for i in range(variants)},
        'native_matches':{str(i):sum(r['native']['passed'] for r in rows if r['target']==i) for i in range(variants)},
        'scope':'Public owned ImageRenderer drawing callback into independently initialized padded CGContext versus pinned native cgImage and rational/float source predictions. No Canvas wire or general color-model claim.'}
