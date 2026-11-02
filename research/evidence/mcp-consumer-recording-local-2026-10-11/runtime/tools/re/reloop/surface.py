"""Owned local IOSurface resource/stride oracle, independently checked in Python."""
import base64
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.verification import bytes_equal

CASES=((1,1,0),(3,2,7),(17,3,129),(33,7,255))


def expected(width,height,stride,seed):
    if any(type(v) is not int for v in (width,height,stride,seed)) or not 1<=width<=64 or not 1<=height<=16 or not width*4<=stride<=65536 or not 0<=seed<=255:
        raise ValueError('Invalid surface geometry')
    raw=bytearray([0xa5])*(stride*height)
    for y in range(height):
        for x in range(width):
            for c in range(4):raw[y*stride+x*4+c]=255 if c==3 else (seed+x*17+y*31+c*53)&255
    return bytes(raw)


def inspect(result,case):
    width,height,seed=case
    try:
        if any(type(result[k]) is not int or result[k]!=v for k,v in [('width',width),('height',height),('seed',seed),('bytes_per_element',4),('pixel_format',0x42475241),('plane_count',0)]):return {'passed':False,'failure':'metadata'}
        raw=expected(width,height,result['stride'],seed);after=bytearray(raw);after[0]^=0x5a
        if type(result['allocation_bytes']) is not int or not len(raw)<=result['allocation_bytes']<=1024*1024:return {'passed':False,'failure':'allocation'}
        before=base64.b64decode(result['before_base64'],validate=True);actual=base64.b64decode(result['after_base64'],validate=True)
        passed=before==raw and actual==bytes(after) and result.get('same_surface_id') is True and result.get('xpc_is_data') is False
        return {'passed':passed,'failure':None if passed else 'resource-or-byte-mismatch','before':before,'after':actual,'expected_before':raw,'expected_after':bytes(after),'padding_bytes_per_row':result['stride']-width*4}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-result'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-surface-probe'
    run(['xcrun','clang','-fobjc-arc','-framework','Foundation','-framework','IOSurface',ROOT/'tools/re/surface_probe.m','-o',target],out,'compile')
    rows=[];failures=0
    for width,height,seed in CASES:
        name='%dx%d-seed%d'%(width,height,seed);records=[]
        for repeat in range(2):
            folder=out/(name+'-'+str(repeat));folder.mkdir()
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                r=subprocess.run([str(target),str(width),str(height),str(seed)],stdout=stdout,stderr=stderr,timeout=10)
            try:value=json.loads((folder/'stdout.json').read_text())
            except ValueError:value={}
            failures+=bool(r.returncode or not value)
            status=inspect(value,(width,height,seed));records.append(status)
            if status['passed']:
                for key in ('before','after','expected_before','expected_after'):(folder/(key+'.bin')).write_bytes(status[key])
                for phase in ('before','after'):atomic(folder/(phase+'-comparison.json'),bytes_equal(folder/(phase+'.bin'),folder/('expected_'+phase+'.bin')))
        rows.append({'case':name,'passed':all(s['passed'] for s in records),'failures':[s['failure'] for s in records],
                     'cross_process_payload_equal':all(s['passed'] for s in records) and records[0]['before']==records[1]['before'] and records[0]['after']==records[1]['after'],
                     'padding_bytes_per_row':records[0].get('padding_bytes_per_row')})
    atomic(out/'surface-corpus.json',{'cases':rows})
    return {'cases':len(rows),'exact_resource_round_trips':sum(r['passed'] for r in rows),'cross_process_payload_equal_cases':sum(r['cross_process_payload_equal'] for r in rows),
            'padded_row_cases':sum((r['padding_bytes_per_row'] or 0)>0 for r in rows),'helper_failures':failures,
            'scope':'Four owned single-plane BGRA surfaces, local XPC reference lifetime and CPU writes. Separate-process bytes checked, not interprocess resource transfer or GPU/canvas semantics.'}
