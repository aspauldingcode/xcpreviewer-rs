"""Seeded UVPropertyList differential corpus and deterministic failure shrinking."""
import base64
import datetime
import json
import pathlib
import plistlib
import random
import subprocess
from reloop.core import ROOT, atomic, digest
from reloop.trace import run
from reloop.verification import bytes_equal, typed


def cases(seed=1, count=24):
    rng=random.Random(seed)
    fixed=[{}, {'empty':'','array':[],'dict':{},'data':b''},
           {'unicode':'🦀 café e\u0301 漢字','null-character':'a\0b'},
           {'integers':[-(2**63),-1,0,1,2**63-1,2**64-1]},
           {'bools':[True,False],'floats':[-0.0,1.25,1e-200,1e200]},
           {'data':bytes(range(256))*256}, {'date':datetime.datetime(2001,1,1)},
           {'deep':{'a':{'b':{'c':{'d':['end']}}}}}]
    for i in range(count):
        if i<len(fixed):yield 'boundary-%02d'%i,fixed[i]
        else:
            yield 'seed-%s-%02d'%(seed,i), {'type':'mutated-owned-probe','value':rng.randint(-(2**31),2**31-1),
                                           'array':[rng.choice([True,False,'', '🦀', rng.random()]) for _ in range(rng.randrange(16))],
                                           'bytes':bytes(rng.getrandbits(8) for _ in range(rng.randrange(1024)))}


def shrink_dictionary(value, fails, budget=30):
    """Delta debugging: remove keys while the SAME failure predicate persists."""
    result=dict(value); attempts=0
    for key in sorted(value):
        if attempts>=budget:break
        candidate={k:v for k,v in result.items() if k!=key};attempts+=1
        if fails(candidate):result=candidate
    return result,attempts


def corpus(out, seed=1, count=24):
    out=pathlib.Path(out)
    target=out/'corpus-probe'
    run(['xcrun','clang','-fobjc-arc','-framework','Foundation',ROOT/'tools/re/plist_probe.m','-o',target],out,'compile')
    results=[];failed=[]
    def probe(name, value):
        folder=out/name;folder.mkdir(exist_ok=True)
        payload=folder/'input.plist';payload.write_bytes(plistlib.dumps(value,fmt=plistlib.FMT_BINARY))
        with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
            p=subprocess.run([str(target),'/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices',str(payload)],stdout=stdout,stderr=stderr,timeout=10)
        try:r=json.loads((folder/'stdout.json').read_text())
        except ValueError:r={}
        decoded=None
        try:decoded=plistlib.loads(base64.b64decode(r['base64']))
        except (KeyError,ValueError,plistlib.InvalidFileException):pass
        comparisons={}
        for key in ['base64','repeat_base64','fresh_base64','foundation_base64']:
            if key in r:
                (folder/(key+'.plist')).write_bytes(base64.b64decode(r[key],validate=True))
        if 'base64' in r:
            for key in ['repeat_base64','fresh_base64','foundation_base64']:
                if key in r:comparisons[key]=bytes_equal(folder/'base64.plist',folder/(key+'.plist'))
            comparisons['python_encoding']=bytes_equal(payload,folder/'base64.plist')
        atomic(folder/'byte-comparisons.json',comparisons)
        return {'case':name,'execution':p.returncode,'uv_equal':r.get('uv_round_trip_equal',False),
                'foundation_equal':r.get('foundation_round_trip_equal',False),'python_equal':decoded is not None and typed(decoded)==typed(value),
                'byte_comparisons':{k:v['passed'] for k,v in comparisons.items()},
                'input_sha256':digest(payload)},folder
    for name,value in cases(seed,count):
        item,folder=probe(name,value)
        replay,replay_folder=probe('replay-'+name,value)
        if (folder/'base64.plist').exists() and (replay_folder/'base64.plist').exists():
            process_comparison=bytes_equal(folder/'base64.plist',replay_folder/'base64.plist')
            atomic(folder/'cross-process-comparison.json',process_comparison)
            item['cross_process_bytes_equal']=process_comparison['passed']
        else:item['cross_process_bytes_equal']=False
        item['replay_typed_values_equal']=replay['execution']==0 and all(replay[k] for k in ['uv_equal','foundation_equal','python_equal'])
        results.append(item)
        if item['execution'] or not all(item[k] for k in ['uv_equal','foundation_equal','python_equal','replay_typed_values_equal']):
            failed.append(name)
            # Shrink only semantic mismatches, not permission/compiler/tool crashes.
            if item['execution']==0:
                failing=next((k for k in ['uv_equal','foundation_equal','python_equal'] if not item[k]),None)
                def fails(candidate):
                    observed,_=probe('shrink-'+name,candidate)
                    return observed['execution']==0 and failing is not None and not observed[failing]
                minimal,attempts=shrink_dictionary(value,fails) if failing else (value,0)
                (folder/'minimal.plist').write_bytes(plistlib.dumps(minimal,fmt=plistlib.FMT_BINARY))
                atomic(folder/'shrink.json',{'attempts':attempts,'keys':list(minimal)})
    atomic(out/'corpus.json',{'seed':seed,'cases':results,'failed':failed})
    return {'cases':len(results),'failed_cases':len(failed),'all_round_trips':not failed,'seed':seed,
            'byte_repeat_equal_cases':sum(r['byte_comparisons'].get('repeat_base64',False) for r in results),
            'byte_fresh_equal_cases':sum(r['byte_comparisons'].get('fresh_base64',False) for r in results),
            'byte_foundation_equal_cases':sum(r['byte_comparisons'].get('foundation_base64',False) for r in results),
            'byte_python_encoding_equal_cases':sum(r['byte_comparisons'].get('python_encoding',False) for r in results),
            'cross_process_bytes_equal_cases':sum(r['cross_process_bytes_equal'] for r in results),
            'scope':'Owned dictionary corpus; no XPC attachments or malformed native object injection.'}
