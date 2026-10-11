"""Bounded local raw-coder class/key controls; no live connection or resources."""
import base64
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run

CLASSES=('NSData','NSString','NSNumber','NSArray','NSDictionary','NSObject')
KEYS=('owned','alternate','data')
DATA=b'owned\0bytes'


def semantic(result):
    # Runtime class-cluster names and exception addresses are diagnostic only.
    return {k:result.get(k) for k in ('outcome','phase','name','matches_requested_class','equals_original','decoded_base64','xpc_tree')}


def assess(results):
    positives=[results['data-'+cls+'-'+key] for cls in CLASSES for key in KEYS]
    def exact_payload(r,payload):
        try:
            tree=r['xpc_tree'];data=tree['items']['data']
            return (tree['type']=='dictionary' and type(tree['count']) is int and tree['count']==1 and set(tree['items'])=={'data'}
                    and data['type']=='data' and type(data['bytes']) is int and data['bytes']==len(payload)
                    and base64.b64decode(data['base64'],validate=True)==payload
                    and base64.b64decode(r['decoded_base64'],validate=True)==payload and r['outcome']=='decoded')
        except (KeyError,ValueError,TypeError):return False
    unsupported=[results[m+'-NSData-owned'] for m in ('string','number','bool','array','dictionary')]
    def nil(mode):return results[mode+'-NSData-owned'].get('outcome')=='nil'
    return {'data_controls':len(positives),'exact_data_controls':sum(exact_payload(r,DATA) for r in positives),
            'class_mismatch_returns_data':sum(exact_payload(results['data-'+cls+'-'+key],DATA) and results['data-'+cls+'-'+key].get('matches_requested_class') is False for cls in CLASSES if cls not in ('NSData','NSObject') for key in KEYS),
            'nondata_encode_exceptions':sum(r.get('outcome')=='exception' and r.get('phase')=='encode' and r.get('name')=='NSInvalidArgumentException' for r in unsupported),
            'empty_data_returns_nil':nil('empty-data'),'nil_object_returns_nil':nil('nil'),'missing_data_returns_nil':nil('missing'),
            'wrong_data_type_returns_nil':nil('wrong-wire-type'),'overwrite_returns_last_data':exact_payload(results['overwrite-NSData-owned'],b'second')}


def matrix(out):
    out=pathlib.Path(out);target=out/'owned-raw-coder'
    run(['xcrun','clang','-fobjc-arc','-fblocks','-framework','Foundation',ROOT/'tools/re/raw_coder_probe.m','-o',target],out,'compile')
    controls=[('data',cls,key) for cls in CLASSES for key in KEYS]+[(mode,'NSData','owned') for mode in ('empty-data','string','number','bool','array','dictionary','nil','missing','wrong-wire-type','overwrite')]
    results={};repeats=0;failures=0;uuids=set()
    for mode,cls,key in controls:
        name='-'.join((mode,cls,key));records=[]
        for repeat in range(2):
            folder=out/(name+'-'+str(repeat));folder.mkdir()
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                r=subprocess.run([str(target),mode,cls,key],stdout=stdout,stderr=stderr,timeout=8)
            try:record=json.loads((folder/'stdout.json').read_text())
            except ValueError:record={}
            if r.returncode or not record:failures+=1
            records.append(record)
            if record.get('encoder_image',{}).get('uuid'):uuids.add(record['encoder_image']['uuid'])
        results[name]=records[0]
        repeats+=bool(records[0] and records[1] and semantic(records[0])==semantic(records[1]))
    observations={**assess(results),'cases':len(controls),'cross_process_semantics_equal':repeats,'helper_failures':failures,'encoder_image_uuids':sorted(uuids),
                  'scope':'Finite owned UVRawXPCCoder/UVRawXPCDecoder object controls. Key/class behavior measured locally; no service IPC, handles or general secure-coder guarantee.'}
    atomic(out/'raw-coder-matrix.json',{'observations':observations,'cases':{k:semantic(v) for k,v in results.items()}})
    return observations
