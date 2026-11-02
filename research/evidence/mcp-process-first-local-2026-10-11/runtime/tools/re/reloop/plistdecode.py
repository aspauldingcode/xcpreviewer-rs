"""Owned UVPropertyList data boundary; separate from Swift optional-value decoding."""
import base64
import json
import pathlib
import plistlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.verification import typed


def fixtures():
    valid=plistlib.dumps({'__unique_service_message_identifier':'owned-🦀'},fmt=plistlib.FMT_BINARY)
    return [('empty-dictionary',plistlib.dumps({},fmt=plistlib.FMT_BINARY),{}),
            ('identifier-dictionary',valid,{'__unique_service_message_identifier':'owned-🦀'}),
            ('empty-data',b'',None),('header-only',b'bplist00',None),
            ('truncated-trailer',valid[:-1],None),('non-plist',b'owned-invalid',None),
            ('array-root',plistlib.dumps(['owned'],fmt=plistlib.FMT_BINARY),['owned']),
            ('string-root',plistlib.dumps('owned',fmt=plistlib.FMT_BINARY),'owned')]


def assess(record,raw,value,exit_code=0):
    if exit_code:return {'passed':False,'failure':'helper-exit'}
    try:
        if base64.b64decode(record['input_base64'],validate=True)!=raw:return {'passed':False,'failure':'input'}
        foundation_value=raw.decode('ascii') if raw in (b'bplist00',b'owned-invalid') else value
        if record['foundation_present'] is not (foundation_value is not None) or record['foundation_dictionary'] is not isinstance(value,dict):return {'passed':False,'failure':'independent-decode'}
        if foundation_value is not None:
            native_foundation=plistlib.loads(base64.b64decode(record['foundation_value_base64'],validate=True))
            if typed(native_foundation)!=typed(foundation_value):return {'passed':False,'failure':'foundation-value'}
        if not isinstance(record['image']['uuid'],str) or not record['image']['uuid']:return {'passed':False,'failure':'identity'}
        exact=record.get('data_present') is True and base64.b64decode(record['data_base64'],validate=True)==raw
        decoded=plistlib.loads(base64.b64decode(record['value_base64'],validate=True)) if 'value_base64' in record else None
        valid_dict=isinstance(value,dict) and record.get('dictionary_type') is True and typed(decoded)==typed(value)
        if isinstance(value,dict) and not valid_dict:return {'passed':False,'failure':'positive-dictionary'}
        if record.get('outcome') not in ('returned','exception'):return {'passed':False,'failure':'outcome'}
        return {'passed':True,'failure':None,'exact_data':exact,'valid_dictionary':valid_dict,'decoded':typed(decoded) if decoded is not None else None,'empty_dictionary':decoded=={} and not isinstance(value,dict)}
    except (KeyError,TypeError,ValueError,plistlib.InvalidFileException):return {'passed':False,'failure':'incomplete-evidence'}


def corpus(out):
    out=pathlib.Path(out);target=out/'plist-decode-probe'
    run(['xcrun','clang','-fobjc-arc','-framework','Foundation',ROOT/'tools/re/plist_decode_probe.m','-o',target],out,'compile')
    rows=[];failures=0;repeats=0;exact=0;positives=0;empty=0
    for name,raw,value in fixtures():
        observations=[];checks=[]
        for repeat in range(2):
            folder=out/(name+'-'+str(repeat));folder.mkdir();fixture=folder/'input.bin';fixture.write_bytes(raw)
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                result=subprocess.run([str(target),str(fixture)],stdout=stdout,stderr=stderr,timeout=8)
            try:record=json.loads((folder/'stdout.json').read_text())
            except ValueError:record={}
            check=assess(record,raw,value,result.returncode);checks.append(check);observations.append(record)
            failures+=not check['passed'];atomic(folder/'assessment.json',check)
        repeats+=all(x['passed'] for x in checks) and observations[0]==observations[1]
        exact+=all(x.get('exact_data',False) for x in checks)
        positives+=all(x.get('valid_dictionary',False) for x in checks)
        empty+=all(x.get('empty_dictionary',False) for x in checks)
        rows.append({'case':name,'observations':observations,'checks':checks})
    atomic(out/'decode-corpus.json',{'cases':rows})
    return {'cases':len(rows),'helper_failures':failures,'repeat_semantics':repeats,'exact_input_bytes':exact,'valid_dictionary_controls':positives,'non_dictionary_empty_controls':empty,
            'scope':'Owned UVPropertyList initWithData/data/dictionary boundary only; not Swift optional identifier acceptance, live reply or full malformed corpus.'}
