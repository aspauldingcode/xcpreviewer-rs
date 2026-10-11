"""Independent literal BGRA and full allocation padding check after GPU completion."""
import base64
import json
import pathlib
import subprocess
from reloop.core import ROOT, atomic
from reloop.trace import run
from reloop.verification import bytes_equal

CASES=((1,1),(3,2),(17,3),(33,7))


def expected(width,height,stride,allocation,stage):
    if any(type(v) is not int for v in (width,height,stride,allocation,stage)) or not 1<=width<=64 or not 1<=height<=16 or not width*4<=stride<=65536 or not stride*height<=allocation<=1048576 or stage not in (-1,0,1,2):
        raise ValueError('Invalid GPU geometry or stage')
    raw=bytearray([0xa5])*allocation
    if stage>=0:
        pixel=b'\xff\x00\x00\xff' if stage==2 else b'\x00\x00\xff\xff'
        for y in range(height):raw[y*stride:y*stride+width*4]=pixel*width
    return bytes(raw)


def inspect(value,case):
    try:
        w,h=case
        for k,n in [('width',w),('height',h),('bytes_per_element',4),('pixel_format',0x42475241),('plane_count',0),('texture_storage_mode',0)]:
            if type(value[k]) is not int or value[k]!=n:raise ValueError('Metadata mismatch')
        if value['same_surface'] is not True or value['unified_memory'] is not True:raise ValueError('Resource identity/storage mismatch')
        stride,allocation=value['stride'],value['allocation_bytes']
        actual=[base64.b64decode(value['before_base64'],validate=True)]
        wanted=[expected(w,h,stride,allocation,-1)]
        if len(value['frames'])!=3:raise ValueError('Incomplete GPU frames')
        for stage,frame in enumerate(value['frames']):
            for k,n in [('stage',stage),('callback_count',1),('callback_status',4),('status',4)]:
                if type(frame[k]) is not int or frame[k]!=n:raise ValueError('Completion evidence mismatch')
            if frame['error_absent'] is not True:raise ValueError('GPU error')
            actual.append(base64.b64decode(frame['bytes_base64'],validate=True));wanted.append(expected(w,h,stride,allocation,stage))
        actual.append(base64.b64decode(value['after_metal_drop_base64'],validate=True));wanted.append(expected(w,h,stride,allocation,2))
        return {'passed':actual==wanted,'failure':None if actual==wanted else 'full-allocation-mismatch','actual':actual,'expected':wanted,
                'allocation_bytes':allocation,'padding_bytes':allocation-w*h*4}
    except (ValueError,KeyError,TypeError):return {'passed':False,'failure':'invalid-result'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-gpu-surface'
    run(['xcrun','clang','-fobjc-arc','-framework','Foundation','-framework','Metal','-framework','IOSurface',ROOT/'tools/re/surface_gpu_probe.m','-o',target],out,'compile')
    rows=[];failures=0;checked_bytes=0
    for case in CASES:
        records=[]
        for repeat in range(2):
            folder=out/('%dx%d-%d'%(*case,repeat));folder.mkdir()
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                result=subprocess.run([str(target),*map(str,case)],stdout=stdout,stderr=stderr,timeout=15)
            try:value=json.loads((folder/'stdout.json').read_text())
            except ValueError:value={}
            status=inspect(value,case);status['passed']=status['passed'] and result.returncode==0
            if result.returncode:status['failure']='helper-exit-'+str(result.returncode)
            failures+=bool(result.returncode or not status['passed']);records.append(status)
            for stage,(actual,wanted) in enumerate(zip(status.get('actual',[]),status.get('expected',[]))):
                (folder/f'actual-{stage}.bin').write_bytes(actual);(folder/f'expected-{stage}.bin').write_bytes(wanted)
                atomic(folder/f'comparison-{stage}.json',bytes_equal(folder/f'actual-{stage}.bin',folder/f'expected-{stage}.bin'));checked_bytes+=len(wanted)
        rows.append({'case':list(case),'passed':all(r['passed'] for r in records),
                     'repeat_equal':all(r['passed'] for r in records) and records[0]['actual']==records[1]['actual'],
                     'failures':[r['failure'] for r in records],'padding_bytes':records[0].get('padding_bytes')})
    atomic(out/'gpu-surface-corpus.json',{'cases':rows})
    return {'cases':len(rows),'passed_cases':sum(r['passed'] for r in rows),'repeat_equal_cases':sum(r['repeat_equal'] for r in rows),
            'helper_failures':failures,'compared_bytes':checked_bytes,'retained_surface_cases':sum(r['passed'] for r in rows),
            'scope':'Owned single-process shared BGRA8 render-clear surfaces on unified memory; full allocation including padding and read after explicit Metal reference drop. No GPU Mach handoff, Canvas synchronization, timeout recovery or reclamation claim.'}
