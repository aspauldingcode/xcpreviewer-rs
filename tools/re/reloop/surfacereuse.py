"""Controlled mutable resource reuse versus separate frame storage, not Canvas wire recovery."""
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.surface import CASES,expected
from reloop.verification import bytes_equal

PHASES=('producer-first','producer-next','delayed-first','second','after-right-release')


def inspect(record,receiver,case,mode,payloads,returncode=0):
    if returncode:return {'passed':False,'failure':'helper-exit'}
    try:
        width,height,seed=case;same=mode=='reuse'
        if mode not in ('reuse','separate') or record.get('mode')!=mode:return {'passed':False,'failure':'mode'}
        for key,value in [('width',width),('height',height),('seed',seed),('next_seed',(seed+1)&255),('receiver_exit',0)]:
            if type(record[key]) is not int or record[key]!=value:return {'passed':False,'failure':'metadata'}
        if any(record.get(k) is not True for k in ('audit_peer_verified','delayed_read_after_second_import','rendezvous_removed')):return {'passed':False,'failure':'lifecycle'}
        if any(type(record[k]) is not int or record[k]<=1 for k in ('sender_pid','receiver_pid')) or record['sender_pid']==record['receiver_pid'] or receiver.get('receiver_pid')!=record['receiver_pid']:return {'passed':False,'failure':'peer-identity'}
        for key in ('first_id','second_id'):
            if type(record[key]) is not int or record[key]<=0 or type(receiver.get(key)) is not int or receiver[key]!=record[key]:return {'passed':False,'failure':'resource-identity'}
        if (record['first_id']==record['second_id'])!=same or receiver.get('port_names_equal') is not same:return {'passed':False,'failure':'resource-identity'}
        if receiver.get('audit_peer_verified') is not True or receiver.get('received_rights_released') is not True:return {'passed':False,'failure':'release'}
        for key,value in [('first_refs_after_two_imports',2 if same else 1),('second_refs_after_first_release',1)]:
            if type(receiver.get(key)) is not int or receiver[key]!=value:return {'passed':False,'failure':'right-counts'}
        if receiver.get('fixture_generations')!=[1,2] or any(type(v) is not int for v in receiver['fixture_generations']):return {'passed':False,'failure':'fixture-generation'}
        first=expected(width,height,record['stride'],seed);second=expected(width,height,record['stride'],(seed+1)&255)
        delayed=second if same else first
        refs=dict(zip(PHASES,(first,second,delayed,second,delayed)))
        if set(payloads)!=set(refs) or any(payloads[k]!=refs[k] for k in refs):return {'passed':False,'failure':'byte-mismatch'}
        if first==second:return {'passed':False,'failure':'no-positive-change'}
        return {'passed':True,'failure':None,'expected':refs,'old_handle_sees_new_frame':same,'padding_bytes_per_row':record['stride']-width*4}
    except (KeyError,TypeError,ValueError):return {'passed':False,'failure':'invalid-result'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-surface-reuse'
    run(['xcrun','clang','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_reuse_probe.c','-o',target],out,'compile')
    rows=[];failures=0
    for case in CASES:
        for mode in ('reuse','separate'):
            results=[];name='%dx%d-seed%d-%s'%(*case,mode)
            for repeat in range(2):
                folder=out/(name+'-'+str(repeat));folder.mkdir()
                with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    result=subprocess.run([str(target),*(str(v) for v in case),mode,str(folder)],stdout=stdout,stderr=stderr,timeout=15)
                try:record=json.loads((folder/'stdout.json').read_text());receiver=json.loads((folder/'receiver.json').read_text())
                except (ValueError,FileNotFoundError):record={};receiver={}
                failures+=bool(result.returncode or not record or not receiver)
                payloads={phase:(folder/(phase+'.bin')).read_bytes() for phase in PHASES if (folder/(phase+'.bin')).exists()}
                check=inspect(record,receiver,case,mode,payloads,result.returncode);results.append((check,payloads))
                if check['passed']:
                    for phase,raw in check['expected'].items():
                        (folder/('expected-'+phase+'.bin')).write_bytes(raw)
                        atomic(folder/(phase+'-comparison.json'),bytes_equal(folder/(phase+'.bin'),folder/('expected-'+phase+'.bin')))
                atomic(folder/'assessment.json',{k:v for k,v in check.items() if k!='expected'})
            passed=all(r[0]['passed'] for r in results)
            rows.append({'case':name,'mode':mode,'passed':passed,'repeat_bytes_equal':passed and results[0][1]==results[1][1],'failures':[r[0]['failure'] for r in results]})
    atomic(out/'surface-reuse-corpus.json',{'cases':rows})
    return {'cases':len(rows),'verified_reuse_cases':sum(r['passed'] for r in rows),'mutable_old_handle_cases':sum(r['passed'] and r['mode']=='reuse' for r in rows),
            'separate_storage_preserved_cases':sum(r['passed'] and r['mode']=='separate' for r in rows),'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),'helper_failures':failures,
            'scope':'Owned audit-verified CPU fixture. Producer-assigned generations and delayed reads demonstrate mutable shared storage versus separate surfaces, with received Mach-right accounting. Not recovered Canvas generation/acknowledgement protocol, GPU fences, stale-name security or final reclamation.'}
