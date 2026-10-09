"""Owned failed handoff controls; expected failure is not preview completion."""
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.surface import CASES,expected
from reloop.verification import bytes_equal

PHASES=('before-transfer','after-import','before-ack')
FLAGS=('audit_peer_verified','failure_observed','local_resource_name_removed','peer_endpoint_name_removed','rendezvous_removed')
# Pinned Darwin SDK constants, independently enforced by the C helper's named constants.
ERRORS={'before-transfer':0x10000003,'after-import':0,'before-ack':0x10004003}


def inspect(record,case,phase,payloads,returncode=0):
    if returncode!=0:return {'passed':False,'failure':'helper-exit'}
    width,height,seed=case
    try:
        if phase not in PHASES or record.get('phase')!=phase:return {'passed':False,'failure':'phase'}
        for key,value in [('width',width),('height',height),('seed',seed),('mach_error',ERRORS[phase]),
                          ('peer_exit',-1 if phase=='before-ack' else 41 if phase=='before-transfer' else 42),
                          ('peer_signal',9 if phase=='before-ack' else 0),('local_resource_refs_retained',1)]:
            if type(record[key]) is not int or record[key]!=value:return {'passed':False,'failure':'metadata-or-rights'}
        if record.get('completion_accepted') is not False or any(record.get(k) is not True for k in FLAGS):return {'passed':False,'failure':'lifecycle'}
        if record.get('receiver_cleanup')!=('process-teardown' if phase=='before-ack' else 'explicit'):return {'passed':False,'failure':'cleanup-path'}
        if any(type(record[k]) is not int or record[k]<=1 for k in ('sender_pid','receiver_pid')) or record['sender_pid']==record['receiver_pid']:return {'passed':False,'failure':'peer-identity'}
        raw=expected(width,height,record['stride'],seed)
        refs={'retained':raw}
        if phase!='before-transfer':refs['imported']=raw
        if set(payloads)!=set(refs) or any(payloads[k]!=refs[k] for k in refs):return {'passed':False,'failure':'byte-mismatch'}
        return {'passed':True,'failure':None,'expected':refs,'padding_bytes_per_row':record['stride']-width*4}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-result'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-surface-failure'
    run(['xcrun','clang','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_failure_probe.c','-o',target],out,'compile')
    rows=[];helper_failures=0
    for case in CASES:
        for phase in PHASES:
            records=[];width,height,seed=case;name='%dx%d-seed%d-%s'%(width,height,seed,phase)
            for repeat in range(2):
                folder=out/(name+'-'+str(repeat));folder.mkdir()
                with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    result=subprocess.run([str(target),str(width),str(height),str(seed),phase,str(folder)],stdout=stdout,stderr=stderr,timeout=15)
                try:record=json.loads((folder/'stdout.json').read_text())
                except ValueError:record={}
                helper_failures+=bool(result.returncode or not record)
                payloads={p.stem:p.read_bytes() for p in folder.glob('*.bin')}
                checked=inspect(record,case,phase,payloads,result.returncode);records.append((checked,payloads))
                if checked['passed']:
                    for stage,raw in checked['expected'].items():
                        (folder/('expected-'+stage+'.bin')).write_bytes(raw)
                        atomic(folder/(stage+'-comparison.json'),bytes_equal(folder/(stage+'.bin'),folder/('expected-'+stage+'.bin')))
                atomic(folder/'assessment.json',{k:v for k,v in checked.items() if k!='expected'})
            passed=all(r[0]['passed'] for r in records)
            rows.append({'case':name,'phase':phase,'passed':passed,'repeat_bytes_equal':passed and records[0][1]==records[1][1],'failures':[r[0]['failure'] for r in records]})
    atomic(out/'surface-failure-corpus.json',{'cases':rows})
    return {'cases':len(rows),'verified_fault_cases':sum(r['passed'] for r in rows),
            'closed_endpoint_cases':sum(r['passed'] and r['phase']=='before-transfer' for r in rows),
            'after_import_error_cases':sum(r['passed'] and r['phase']=='after-import' for r in rows),
            'completion_timeout_cases':sum(r['passed'] and r['phase']=='before-ack' for r in rows),
            'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),'helper_failures':helper_failures,
            'scope':'Owned CPU Mach fixture: closed endpoint, explicit import-error cleanup and completion timeout with owned-child SIGKILL. Local names/right counts only; no final kernel reclamation, general crash/race coverage, GPU completion or Apple Canvas XPC claim.'}


def inspect_use(record,case,payload,returncode=0):
    if returncode:return {'passed':False,'failure':'helper-exit'}
    try:
        for key,value in zip(('width','height','seed'),case):
            if type(record[key]) is not int or record[key]!=value:return {'passed':False,'failure':'metadata'}
        if record.get('phase')!='use-state' or record.get('mach_port_name_removed') is not True or record.get('cf_reference_retained') is not True:return {'passed':False,'failure':'lifecycle'}
        for key,values in [('local_use_counts',[0,0,1,1,0]),('global_in_use',[0,1,1,1,0])]:
            if record.get(key)!=values or any(type(v) is not int for v in record[key]):return {'passed':False,'failure':'use-state'}
        raw=expected(case[0],case[1],record['stride'],case[2])
        if payload!=raw:return {'passed':False,'failure':'byte-mismatch'}
        return {'passed':True,'failure':None,'expected':raw}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-result'}


def use_corpus(out):
    out=pathlib.Path(out);target=out/'owned-surface-use-state'
    run(['xcrun','clang','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_failure_probe.c','-o',target],out,'compile')
    rows=[];failures=0
    for case in CASES:
        records=[]
        for repeat in range(2):
            folder=out/('%dx%d-seed%d-use-state-%d'%(*case,repeat));folder.mkdir()
            with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                result=subprocess.run([str(target),*(str(v) for v in case),'use-state',str(folder)],stdout=stdout,stderr=stderr,timeout=15)
            try:record=json.loads((folder/'stdout.json').read_text())
            except ValueError:record={}
            path=folder/'not-in-use.bin';raw=path.read_bytes() if path.exists() else None
            checked=inspect_use(record,case,raw,result.returncode);failures+=bool(result.returncode or not record)
            records.append((checked,raw))
            if checked['passed']:
                (folder/'expected.bin').write_bytes(checked['expected']);atomic(folder/'comparison.json',bytes_equal(path,folder/'expected.bin'))
            atomic(folder/'assessment.json',{k:v for k,v in checked.items() if k!='expected'})
        passed=all(r[0]['passed'] for r in records)
        rows.append({'geometry':case,'passed':passed,'repeat_bytes_equal':passed and records[0][1]==records[1][1],'failures':[r[0]['failure'] for r in records]})
    atomic(out/'surface-use-corpus.json',{'cases':rows})
    return {'cases':len(rows),'verified_use_state_cases':sum(r['passed'] for r in rows),'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),'helper_failures':failures,
            'scope':'Owned local CPU surfaces: local count differs from global in-use while Mach port lives; global in-use false still permits exact bytes through retained CF reference. No final allocation reclamation or Canvas reuse protocol.'}
