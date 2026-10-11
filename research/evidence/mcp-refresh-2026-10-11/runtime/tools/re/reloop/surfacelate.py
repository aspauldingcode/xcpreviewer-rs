"""Paired owned late-ack controls distinguish receive timeout from endpoint revocation."""
import pathlib
import subprocess
from reloop.core import ROOT,atomic,load
from reloop.trace import run
from reloop.surface import CASES
from reloop.surfacefailure import inspect as inspect_base,LATE_PHASES
from reloop.verification import bytes_equal


def inspect(record,peer,case,phase,payloads,returncode=0):
    checked=inspect_base(record,case,phase,payloads,returncode)
    if not checked['passed']:return checked
    if phase not in LATE_PHASES:return {'passed':False,'failure':'phase'}
    try:
        if record.get('late_ack_received') is not (phase=='late-ack-open'):return {'passed':False,'failure':'late-receive'}
        if peer.get('phase')!=phase:return {'passed':False,'failure':'peer-phase'}
        for key,value in [('sender_pid',record['sender_pid']),('receiver_pid',record['receiver_pid']),
                          ('mach_error',0 if phase=='late-ack-open' else 0x10000003),('resource_refs_before_cleanup',1)]:
            if type(peer[key]) is not int or peer[key]!=value:return {'passed':False,'failure':'peer-metadata-or-rights'}
        for key in ['resource_name_removed','cf_reference_released','inbox_name_removed','reply_name_removed']:
            if peer.get(key) is not True:return {'passed':False,'failure':'peer-cleanup'}
        return checked
    except (KeyError,TypeError):return {'passed':False,'failure':'missing-peer-evidence'}


def corpus(out):
    out=pathlib.Path(out);target=out/'owned-surface-late-ack'
    run(['xcrun','clang','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',ROOT/'tools/re/surface_failure_probe.c','-o',target],out,'compile')
    rows=[];compared=0;failures=0
    for case in CASES:
        for phase in LATE_PHASES:
            records=[]
            for repeat in range(2):
                folder=out/('%dx%d-seed%d-%s-%d'%(*case,phase,repeat));folder.mkdir()
                with (folder/'stdout.json').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    result=subprocess.run([str(target),*(str(v) for v in case),phase,str(folder)],stdout=stdout,stderr=stderr,timeout=15)
                record=load(folder/'stdout.json',{});peer=load(folder/'late-peer.json',{})
                payloads={p.stem:p.read_bytes() for p in folder.glob('*.bin')}
                checked=inspect(record,peer,case,phase,payloads,result.returncode)
                records.append((checked,payloads));failures+=not checked['passed']
                if checked['passed']:
                    for stage,raw in checked['expected'].items():
                        ref=folder/('expected-'+stage+'.bin');ref.write_bytes(raw)
                        atomic(folder/(stage+'-comparison.json'),bytes_equal(ref,folder/(stage+'.bin')));compared+=len(raw)
                atomic(folder/'assessment.json',{k:v for k,v in checked.items() if k!='expected'})
            passed=all(r[0]['passed'] for r in records)
            rows.append({'geometry':case,'phase':phase,'passed':passed,'repeat_bytes_equal':passed and records[0][1]==records[1][1],'failures':[r[0]['failure'] for r in records]})
    atomic(out/'late-ack-corpus.json',{'rows':rows,'compared_bytes':compared})
    return {'cases':len(rows),'verified_late_ack_cases':sum(r['passed'] for r in rows),'repeat_bytes_equal_cases':sum(r['repeat_bytes_equal'] for r in rows),
            'open_endpoint_late_ack_cases':sum(r['passed'] and r['phase']=='late-ack-open' for r in rows),
            'revoked_endpoint_late_ack_cases':sum(r['passed'] and r['phase']=='late-ack-closed' for r in rows),'compared_bytes':compared,'failed_executions':failures,
            'scope':'Owned CPU Mach fixture, receive timeout then live-peer late ack, open versus explicitly revoked reply endpoint. Explicit cleanup, exact padded pixels; no native Canvas timeout policy, final reclamation, GPU or race guarantee.'}
