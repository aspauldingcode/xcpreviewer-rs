"""Owned sender/receiver Mach surface handoff, exit and exact byte controls."""
import json
import pathlib
import subprocess
from reloop.core import ROOT,atomic
from reloop.trace import run
from reloop.surface import CASES,expected
from reloop.verification import bytes_equal

PHASES=('before','after-exit','after-receiver-mutation')
FLAGS=('different_processes','audit_peer_verified','sender_observed_receiver_mutation','received_port_released_before_sender_exit','survives_sender_exit','receiver_mutation_after_exit','rendezvous_removed')
RECEIVER_PHASES=('before','after-exit','after-owner-mutation','port-only')
RECEIVER_FLAGS=('different_processes','audit_peer_verified','survives_receiver_exit','owner_mutation_after_exit','port_retains_after_owner_release','rendezvous_removed')


def inspect(record,case,mode,payloads):
    width,height,seed=case
    try:
        for key,value in [('width',width),('height',height),('seed',seed),('sender_exit',23 if mode=='abrupt' else 0)]:
            if type(record[key]) is not int or record[key]!=value:return {'passed':False,'failure':'metadata'}
        if mode not in ('clean','abrupt') or record.get('mode')!=mode:return {'passed':False,'failure':'mode'}
        if any(record.get(k) is not True for k in FLAGS):return {'passed':False,'failure':'lifecycle'}
        if any(type(record[k]) is not int or record[k]<=1 for k in ('sender_pid','receiver_pid')) or record['sender_pid']==record['receiver_pid']:return {'passed':False,'failure':'peer-identity'}
        raw=expected(width,height,record['stride'],seed);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
        refs=dict(zip(PHASES,(raw,bytes(after),bytes(final))))
        if set(payloads)!=set(PHASES) or any(payloads[k]!=refs[k] for k in PHASES):return {'passed':False,'failure':'byte-mismatch'}
        return {'passed':True,'failure':None,'expected':refs,'padding_bytes_per_row':record['stride']-width*4}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-result'}


def inspect_receiver(record,case,mode,payloads,expect=expected):
    width,height,seed=case
    try:
        if mode not in ('receiver-clean','receiver-abrupt') or record.get('mode')!=mode:return {'passed':False,'failure':'mode'}
        for key,value in [('width',width),('height',height),('seed',seed),('receiver_exit',23 if mode=='receiver-abrupt' else 0),
                          ('sender_send_refs_before',1),('sender_send_refs_after_copy',1),('sender_send_refs_after_exit',1),('sender_send_refs_after_release',0)]:
            if type(record[key]) is not int or record[key]!=value:return {'passed':False,'failure':'metadata-or-rights'}
        if any(record.get(k) is not True for k in RECEIVER_FLAGS):return {'passed':False,'failure':'lifecycle'}
        if record.get('receiver_release')!=('process-teardown' if mode=='receiver-abrupt' else 'explicit-port-and-cf'):return {'passed':False,'failure':'release-path'}
        if any(type(record[k]) is not int or record[k]<=1 for k in ('sender_pid','receiver_pid')) or record['sender_pid']==record['receiver_pid']:return {'passed':False,'failure':'peer-identity'}
        raw=expect(width,height,record['stride'],seed);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
        refs=dict(zip(RECEIVER_PHASES,(raw,bytes(after),bytes(final),bytes(final))))
        if set(payloads)!=set(RECEIVER_PHASES) or any(payloads[k]!=refs[k] for k in RECEIVER_PHASES):return {'passed':False,'failure':'byte-mismatch'}
        return {'passed':True,'failure':None,'expected':refs,'padding_bytes_per_row':record['stride']-width*4}
    except (KeyError,ValueError,TypeError):return {'passed':False,'failure':'invalid-result'}


def corpus(out,exit_order='sender'):
    if exit_order not in ('sender','receiver'):raise ValueError('exit_order must be sender or receiver')
    receiver=exit_order=='receiver';phases=RECEIVER_PHASES if receiver else PHASES
    check=inspect_receiver if receiver else inspect
    out=pathlib.Path(out);target=out/'owned-surface-ipc'
    run(['xcrun','clang','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_ipc_probe.c','-o',target],out,'compile')
    rows=[];failures=0
    for case in CASES:
        for mode in (('receiver-clean','receiver-abrupt') if receiver else ('clean','abrupt')):
            width,height,seed=case;name='%dx%d-seed%d-%s'%(width,height,seed,mode);records=[]
            for repeat in range(2):
                folder=out/(name+'-'+str(repeat));folder.mkdir()
                with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    result=subprocess.run([str(target),str(width),str(height),str(seed),mode,str(folder)],stdout=stdout,stderr=stderr,timeout=15)
                try:record=json.loads((folder/'stdout.json').read_text())
                except ValueError:record={}
                failures+=bool(result.returncode or not record)
                payloads={phase:(folder/(phase+'.bin')).read_bytes() for phase in phases if (folder/(phase+'.bin')).exists()}
                checked=check(record,case,mode,payloads)
                if result.returncode:checked={'passed':False,'failure':'helper-exit'}
                records.append((checked,payloads))
                if checked['passed']:
                    for phase,raw in checked['expected'].items():
                        (folder/('expected-'+phase+'.bin')).write_bytes(raw)
                        atomic(folder/(phase+'-comparison.json'),bytes_equal(folder/(phase+'.bin'),folder/('expected-'+phase+'.bin')))
                atomic(folder/'assessment.json',{k:v for k,v in checked.items() if k!='expected'})
            passed=all(c[0]['passed'] for c in records)
            rows.append({'case':name,'mode':mode,'passed':passed,'repeat_bytes_equal':passed and records[0][1]==records[1][1],
                         'failures':[c[0]['failure'] for c in records],'padding_bytes_per_row':records[0][0].get('padding_bytes_per_row')})
    atomic(out/'surface-ipc-corpus.json',{'cases':rows})
    if receiver:
        return {'cases':len(rows),'exact_receiver_exit_cases':sum(r['passed'] for r in rows),
                'clean_receiver_exit_cases':sum(r['passed'] and r['mode']=='receiver-clean' for r in rows),
                'abrupt_receiver_exit_cases':sum(r['passed'] and r['mode']=='receiver-abrupt' for r in rows),
                'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),'helper_failures':failures,
                'scope':'Owned audit-verified receiver-first exit; local send-right counts and retained Mach-port access after owner CF release. No final kernel reclamation, GPU fences, concurrent release race or Apple XPC envelope.'}
    return {'cases':len(rows),'exact_handoff_cases':sum(r['passed'] for r in rows),'clean_sender_exit_cases':sum(r['passed'] and r['mode']=='clean' for r in rows),
            'abrupt_sender_exit_cases':sum(r['passed'] and r['mode']=='abrupt' for r in rows),'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),
            'helper_failures':failures,'scope':'Owned fork/exec sender/receiver Mach-port transfers, audit-verified peers, single-plane CPU BGRA. No Apple XPC envelope, GPU fences, canvas capture or surface revocation guarantee.'}
