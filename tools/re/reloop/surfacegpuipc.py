"""Completion-gated owned GPU producer with audited receiver-first Mach handoff."""
import base64
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.surface import CASES
from reloop.surfacegpu import expected
from reloop.surfaceipc import inspect_receiver,RECEIVER_PHASES
from reloop.verification import bytes_equal


def inspect(record,producer,case,mode,payloads):
    try:
        w,h,seed=case
        for k,n in [('producer_pid',record['sender_pid']),('surface_id',record['surface_id']),('width',w),('height',h),('stride',record['stride']),('allocation_bytes',record['snapshot_bytes']),('callback_count',1),('callback_status',4),('status',4),('storage_mode',0)]:
            if type(producer[k]) is not int or type(n) is not int or producer[k]!=n:raise ValueError('GPU identity/completion mismatch')
        if producer['surface_id']<=0 or producer['producer_pid']<=1 or producer['error_absent'] is not True or producer['unified_memory'] is not True:raise ValueError('GPU resource/error mismatch')
        allocation=producer['allocation_bytes']
        if allocation>65536:raise ValueError('GPU handoff allocation exceeds owned limit')
        stride=producer['stride'];stage=2 if seed>=128 else 0
        before=base64.b64decode(producer['before_base64'],validate=True);after=base64.b64decode(producer['after_base64'],validate=True)
        initial=expected(w,h,stride,allocation,-1);rendered=expected(w,h,stride,allocation,stage)
        if before!=initial or after!=rendered:raise ValueError('GPU producer allocation mismatch')
        checked=inspect_receiver(record,case,mode,payloads,expect=lambda a,b,c,d:expected(a,b,c,allocation,2 if d>=128 else 0))
        if not checked['passed']:return checked
        checked['expected'].update({'producer-before':initial,'producer-after':rendered})
        checked['producer_payloads']={'producer-before':before,'producer-after':after}
        return checked
    except (KeyError,TypeError,ValueError):return {'passed':False,'failure':'invalid-gpu-producer'}


def corpus(out,consumer=False):
    out=pathlib.Path(out);target=out/'owned-gpu-surface-ipc'
    run(['xcrun','clang','-DRE_GPU_PRODUCER',*(['-DRE_GPU_CONSUMER'] if consumer else []),'-Wall','-Wextra','-fobjc-arc','-framework','Foundation','-framework','Metal','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_ipc_probe.c',ROOT/'tools/re/surface_gpu_producer.m','-o',target],out,'compile')
    rows=[];failures=0;compared=0
    for case in CASES:
        for mode in ('receiver-clean','receiver-abrupt'):
            records=[]
            for repeat in range(2):
                folder=out/('%dx%d-seed%d-%s-%d'%(*case,mode,repeat));folder.mkdir()
                with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    r=subprocess.run([str(target),*map(str,case),mode,str(folder)],stdout=stdout,stderr=stderr,timeout=15)
                def read(name):
                    try:return json.loads((folder/name).read_text())
                    except (ValueError,OSError):return {}
                record=read('stdout.json');producer=read('gpu-producer.json')
                payloads={p:(folder/(p+'.bin')).read_bytes() for p in RECEIVER_PHASES if (folder/(p+'.bin')).exists()}
                checked=inspect(record,producer,case,mode,payloads)
                if consumer and checked['passed']:
                    gpu=inspect_consumer(read('gpu-consumer.json'),record,case)
                    if gpu['passed']:
                        payloads.update(gpu['actual']);checked['expected'].update(gpu['expected'])
                    else:checked=gpu
                if r.returncode:checked={'passed':False,'failure':'helper-exit-'+str(r.returncode)}
                failures+=not checked['passed']
                if checked['passed']:
                    payloads.update(checked.pop('producer_payloads'))
                    for phase,wanted in checked['expected'].items():
                        (folder/(phase+'.bin')).write_bytes(payloads[phase]);(folder/('expected-'+phase+'.bin')).write_bytes(wanted)
                        atomic(folder/(phase+'-comparison.json'),bytes_equal(folder/(phase+'.bin'),folder/('expected-'+phase+'.bin')));compared+=len(wanted)
                atomic(folder/'assessment.json',{k:v for k,v in checked.items() if k not in ('expected','actual')})
                records.append((checked['passed'],payloads))
            rows.append({'case':list(case),'mode':mode,'passed':all(r[0] for r in records),'repeat_equal':all(r[0] for r in records) and records[0][1]==records[1][1]})
    atomic(out/'gpu-ipc-corpus.json',{'cases':rows})
    return {'cases':len(rows),'passed_cases':sum(r['passed'] for r in rows),'repeat_equal_cases':sum(r['repeat_equal'] for r in rows),'helper_failures':failures,'compared_bytes':compared,'gpu_consumer_cases':sum(r['passed'] for r in rows) if consumer else 0,
            'consumer_gpu_readback':consumer,
            'scope':'Owned completed shared-BGRA GPU producer and audited receiver-first Mach surface handoff, full allocation and local sender rights. Optional owned GPU consumer blit is separately flagged; no early-read race, Canvas envelope or final reclamation.'}


def inspect_consumer(value,record,case):
    try:
        w,h,seed=case
        for k,n in [('consumer_pid',record['receiver_pid']),('surface_id',record['surface_id']),('width',w),('height',h),('callback_count',1),('callback_status',4),('status',4),('source_storage_mode',0),('destination_storage_mode',0)]:
            if type(value[k]) is not int or type(n) is not int or value[k]!=n:raise ValueError('GPU consumer identity/completion mismatch')
        if value['error_absent'] is not True or value['unified_memory'] is not True:raise ValueError('Consumer GPU error/storage mismatch')
        if type(value['stride']) is not int or value['stride']!=((w*4+255)&~255) or type(value['allocation_bytes']) is not int or value['allocation_bytes']!=16384:raise ValueError('Consumer destination extent changed')
        stride=value['stride'];allocation=value['allocation_bytes']
        if stride*h>allocation:raise ValueError('Consumer destination too small')
        initial=bytes([0x5c])*allocation;rendered=bytearray(initial)
        pixel=b'\xff\x00\x00\xff' if seed>=128 else b'\x00\x00\xff\xff'
        for y in range(h):rendered[y*stride:y*stride+w*4]=pixel*w
        actual={'consumer-before':base64.b64decode(value['before_base64'],validate=True),'consumer-after':base64.b64decode(value['after_base64'],validate=True)}
        wanted={'consumer-before':initial,'consumer-after':bytes(rendered)}
        return {'passed':actual==wanted,'failure':None if actual==wanted else 'consumer-full-allocation-mismatch','actual':actual,'expected':wanted}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-gpu-consumer'}
