"""Bounded task-local Mach name churn; no arbitrary churn or Canvas guarantee."""
import base64
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.surface import CASES,expected


def inspect(r,case,exitcode=0):
    if exitcode:return {'passed':False,'failure':'helper-exit'}
    try:
        w,h,seed=case
        for k,v in zip(('width','height','seed'),case):
            if type(r[k]) is not int or r[k]!=v:raise ValueError('geometry')
        for k in ('first_id','second_id'):
            if type(r[k]) is not int or r[k]<=0:raise ValueError('identity')
        if r['first_id']==r['second_id']:raise ValueError('identity')
        old=r['old_name'];new=r['replacement_name'];obs=r['observations']
        if type(old) is not int or old<=0 or type(new) is not int or new<=0 or not isinstance(obs,list) or len(obs)!=128:raise ValueError('name-observations')
        for item in obs:
            name=item['name']
            if type(name) is not int or name<=0 or item.get('removed') is not True:raise ValueError('churn-cleanup')
            for key,value in {'current_id':r['second_id'],'stale_id':r['second_id'] if name==old else 0,'send_refs':1}.items():
                if type(item[key]) is not int or item[key]!=value:raise ValueError('churn-identity')
        for k,v in {'live_lookup':r['first_id'],'retired_lookup':0,'stale_lookup':r['second_id'] if new==old else 0,'previous_name_lookup':r['second_id'],'ref_status':0,'send_refs':1,'release_status':0}.items():
            if type(r[k]) is not int or r[k]!=v:raise ValueError(k)
        if r['name_removed'] is not True:raise ValueError('cleanup')
        stride=r['stride'];size=r['allocation']
        if type(size) is not int or not stride*h<=size<=1048576:raise ValueError('allocation')
        first=expected(w,h,stride,seed)+bytes([0xa5])*(size-stride*h)
        second=expected(w,h,stride,(seed+1)&255)+bytes([0xa5])*(size-stride*h)
        payloads={k:base64.b64decode(r[k+'_base64'],validate=True) for k in ('first','second','stale')}
        if payloads!={'first':first,'second':second,'stale':second}:raise ValueError('bytes')
        return {'passed':True,'failure':None,'payloads':payloads,'compared_bytes':3*size,'exact_name_reuse':sum(i['name']==old for i in obs),'index_reuse':sum((i['name']>>8)==(old>>8) for i in obs)}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-evidence'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-name-reuse'
    run(['xcrun','clang','-Wall','-Wextra','-fobjc-arc','-framework','Foundation','-framework','IOSurface',ROOT/'tools/re/surface_name_reuse.m','-o',target],out,'compile')
    rows=[]
    for case in CASES:
        records=[]
        for repeat in range(2):
            folder=out/('%dx%d-seed%d-%d'%(*case,repeat));folder.mkdir()
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                p=subprocess.run([str(target),*map(str,case)],stdout=stdout,stderr=stderr,timeout=10)
            atomic(folder/'exit-status.json',{'returncode':p.returncode})
            try:r=json.loads((folder/'stdout.json').read_text())
            except ValueError:r={}
            check=inspect(r,case,p.returncode);records.append(check)
            for key,raw in check.get('payloads',{}).items():(folder/(key+'.bin')).write_bytes(raw)
        rows.append({'passed':all(r['passed'] for r in records),'repeat_equal':all(r['passed'] for r in records) and records[0]['payloads']==records[1]['payloads'],'compared_bytes':sum(r.get('compared_bytes',0) for r in records),'exact_name_reuse':sum(r.get('exact_name_reuse',0) for r in records),'index_reuse':sum(r.get('index_reuse',0) for r in records),'failures':[r['failure'] for r in records]})
    atomic(out/'name-reuse.json',{'cases':rows})
    return {'verified_cases':sum(r['passed'] for r in rows),'repeat_equal_cases':sum(r['repeat_equal'] for r in rows),'compared_bytes':sum(r['compared_bytes'] for r in rows),'exact_name_reuse':sum(r['exact_name_reuse'] for r in rows),'index_reuse':sum(r['index_reuse'] for r in rows),'scope':'Owned task-local 128 sequential replacement send-right create/lookups/deallocations per execution; full CPU allocations including padding/tail. Numeric index is name>>8 observation, no arbitrary reuse guarantee, Canvas transport, GPU race or physical reclamation.'}
