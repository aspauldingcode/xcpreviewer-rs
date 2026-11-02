"""Owned XPC object experiments; never opens a connection or transfers resources."""
import base64
import json
import pathlib
import plistlib
import subprocess
from reloop.core import ROOT, atomic, digest
from reloop.corpus import cases, shrink_dictionary
from reloop.trace import run
from reloop.verification import bytes_equal, typed


def inspect_result(result, expected):
    if result.get('outcome') != 'decoded': return {'failure': 'not-decoded'}
    tree=result.get('xpc_tree',{})
    if tree.get('type')!='dictionary' or tree.get('count')!=1 or set(tree.get('items',{}))!={'data'}:
        return {'failure':'wrapper-shape'}
    item=tree['items']['data']
    if item.get('truncated'): return {'failure':'capture-truncated'}
    if item.get('type')!='data': return {'failure':'payload-type'}
    try:
        payload=base64.b64decode(item['base64'],validate=True)
        uv=base64.b64decode(result['uv_data_base64'],validate=True)
        decoded=plistlib.loads(base64.b64decode(result['decoded_base64'],validate=True))
        independent=plistlib.loads(payload)
    except (KeyError,ValueError,plistlib.InvalidFileException,OverflowError):return {'failure':'invalid-payload'}
    if len(payload)!=item.get('bytes'):return {'failure':'payload-length'}
    if typed(decoded)!=typed(expected) or typed(independent)!=typed(expected) or result.get('round_trip_equal') is not True:
        return {'failure':'typed-mismatch'}
    return {'failure':None if payload==uv else 'byte-mismatch', 'data_wrapper':True,
            'payload_equals_uv_data':payload==uv,'typed_equal':True,'payload':payload,'uv_data':uv}


def compile_probe(out):
    target=out/'owned-xpc-probe'
    run(['xcrun','clang','-fobjc-arc','-fblocks','-framework','Foundation',ROOT/'tools/re/xpc_probe.m','-o',target],out,'compile')
    return target


def probe(target,out,name,value,mode='roundtrip'):
    folder=out/name;folder.mkdir(exist_ok=True)
    fixture=folder/'input.plist';fixture.write_bytes(plistlib.dumps(value,fmt=plistlib.FMT_BINARY))
    with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
        completed=subprocess.run([str(target),str(fixture),mode],stdout=stdout,stderr=stderr,timeout=10)
    try:result=json.loads((folder/'stdout.json').read_text())
    except ValueError:result={}
    return folder,result,completed.returncode


def corpus(out,seed=9,count=32):
    out=pathlib.Path(out);target=compile_probe(out);results=[];uuids=set()
    for name,value in cases(seed,count):
        folder,result,code=probe(target,out,name,value)
        status=inspect_result(result,value) if code==0 else {'failure':'execution-failure'}
        _,replay,replay_code=probe(target,out,'replay-'+name,value)
        repeat=inspect_result(replay,value) if replay_code==0 else {'failure':'execution-failure'}
        item={'case':name,'execution':code,'failure':status.get('failure'),
              'replay_failure':repeat.get('failure'),'data_wrapper':status.get('data_wrapper',False),
              'payload_equals_uv_data':status.get('payload_equals_uv_data',False),
              'typed_equal':status.get('typed_equal',False) and repeat.get('typed_equal',False),
              'cross_process_bytes_equal':False,'input_sha256':digest(folder/'input.plist')}
        for key in ['payload','uv_data']:
            if key in status:(folder/(key+'.plist')).write_bytes(status[key])
        if 'payload' in status and 'payload' in repeat:
            (folder/'replay-payload.plist').write_bytes(repeat['payload'])
            comparison=bytes_equal(folder/'payload.plist',folder/'replay-payload.plist')
            atomic(folder/'cross-process-comparison.json',comparison);item['cross_process_bytes_equal']=comparison['passed']
        if result.get('encoder_image',{}).get('uuid'):uuids.add(result['encoder_image']['uuid'])
        if status.get('failure') in {'wrapper-shape','payload-type','payload-length','typed-mismatch','byte-mismatch'}:
            failure=status['failure']
            def fails(candidate):
                _,r,c=probe(target,out,'shrink-'+name,candidate)
                return c==0 and inspect_result(r,candidate).get('failure')==failure
            minimal,attempts=shrink_dictionary(value,fails,budget=8)
            (folder/'minimal.plist').write_bytes(plistlib.dumps(minimal,fmt=plistlib.FMT_BINARY))
            atomic(folder/'shrink.json',{'failure':failure,'attempts':attempts})
        results.append(item)
    atomic(out/'xpc-corpus.json',{'seed':seed,'cases':results,'encoder_image_uuids':sorted(uuids)})
    failed=[r['case'] for r in results if r['failure'] or r['replay_failure']]
    return {'cases':len(results),'failed_cases':len(failed),'all_typed_round_trips':all(r['typed_equal'] for r in results),
            'data_wrapper_cases':sum(r['data_wrapper'] for r in results),
            'payload_equals_uv_data_cases':sum(r['payload_equals_uv_data'] for r in results),
            'cross_process_bytes_equal_cases':sum(r['cross_process_bytes_equal'] for r in results),
            'encoder_image_uuids':sorted(uuids),'seed':seed,
            'scope':'Owned property-list dictionaries encoded into local XPC objects. No live IPC, handles, resources or service connections.'}


def negatives(out):
    out=pathlib.Path(out);target=compile_probe(out);value=list(cases(9,3))[2][1];results={}
    for mode in ['missing-data','wrong-type','truncated-data','extra-key','prefix-0','direct-prefix-0','direct-prefix-8','direct-prefix-104']:
        _,result,code=probe(target,out,mode,value,mode)
        equal=False
        if code==0 and result.get('decoded_base64'):
            try:equal=typed(plistlib.loads(base64.b64decode(result['decoded_base64'],validate=True)))==typed(value)
            except (ValueError,plistlib.InvalidFileException):pass
        results[mode]={'execution':code,'outcome':result.get('outcome','process-signal' if code<0 else 'invalid-result'),
                       'typed_equal':equal,'decoded_empty_dictionary':result.get('decoded_empty_dictionary',False),'exception':result.get('name')}
    atomic(out/'negative-envelopes.json',results)
    invalid=[results[m] for m in ['missing-data','wrong-type','truncated-data']]
    return {'modes':results,'invalid_rejected_without_crash':all(r['execution']==0 and r['outcome'] in {'nil','exception'} for r in invalid),
            'extra_key_preserves_values':results['extra-key']['execution']==0 and results['extra-key']['typed_equal'],
            'truncated_data_decodes_empty_dictionary':results['truncated-data']['execution']==0 and results['truncated-data']['decoded_empty_dictionary'],
            'missing_data_returns_nil':results['missing-data']['execution']==0 and results['missing-data']['outcome']=='nil',
            'wrong_type_returns_nil':results['wrong-type']['execution']==0 and results['wrong-type']['outcome']=='nil',
            'direct_full_preserves_values':results['direct-prefix-104']['execution']==0 and results['direct-prefix-104']['typed_equal'],
            'direct_eight_byte_decodes_empty':results['direct-prefix-8']['execution']==0 and results['direct-prefix-8']['decoded_empty_dictionary'],
            'empty_route_outcomes_differ':results['prefix-0']['execution']==0 and results['direct-prefix-0']['execution']==0 and results['prefix-0']['outcome']!=results['direct-prefix-0']['outcome'],
            'scope':'Malformed owned XPC dictionaries in isolated helpers; failures are observations, not service traffic.'}


def prefixes(out):
    out=pathlib.Path(out);target=compile_probe(out);value=list(cases(9,3))[2][1]
    _,reference,code=probe(target,out,'reference',value)
    if code or inspect_result(reference,value).get('failure'):raise RuntimeError('Valid XPC reference failed')
    full=base64.b64decode(reference['uv_data_base64'],validate=True)
    if len(full)>512:raise RuntimeError('Prefix sweep reference exceeds experiment bound')
    results=[]
    for length in range(len(full)+1):
        _,r,code=probe(target,out,'prefix-%03d'%length,value,'prefix-'+str(length))
        preserved=False
        try:preserved=typed(plistlib.loads(base64.b64decode(r['decoded_base64'],validate=True)))==typed(value)
        except (KeyError,ValueError,plistlib.InvalidFileException):pass
        results.append({'prefix_bytes':length,'execution':code,'outcome':r.get('outcome','process-signal' if code<0 else 'invalid-result'),
                        'preserves_values':preserved,'decoded_empty_dictionary':r.get('decoded_empty_dictionary',False)})
    atomic(out/'prefix-sweep.json',{'full_bytes':len(full),'results':results})
    def fails(candidate):
        _,r,c=probe(target,out,'shrink-truncated',candidate,'truncated-data')
        return c==0 and r.get('decoded_empty_dictionary') is True and r.get('round_trip_equal') is False
    minimal,attempts=shrink_dictionary(value,fails,budget=8)
    (out/'minimal-input.plist').write_bytes(plistlib.dumps(minimal,fmt=plistlib.FMT_BINARY))
    atomic(out/'minimized.json',{'keys':sorted(minimal),'attempts':attempts,'failure_preserved':fails(minimal)})
    return {'tested_prefixes':len(results),'full_bytes':len(full),'full_prefix_preserves_values':results[-1]['preserves_values'],
            'incomplete_prefixes_preserving_values':sum(r['preserves_values'] for r in results[:-1]),
            'incomplete_prefixes_decoded_empty':sum(r['decoded_empty_dictionary'] for r in results[:-1]),
            'incomplete_prefixes_nil':sum(r['outcome']=='nil' for r in results[:-1]),
            'helper_failures':sum(r['execution']!=0 for r in results),
            'minimal_keys':len(minimal),'minimal_failure_preserved':fails(minimal),
            'scope':'Every prefix of one owned 104-byte Unicode plist; not all malformed plists or live XPC traffic.'}
