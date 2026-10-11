"""Discriminating owned compiler/cache interruption experiment."""
import sys
import time
from reloop.core import ROOT, atomic, digest, execute


def hashes(folder):
    return {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and not p.is_symlink()}


def corpus(out):
    cases=[]
    for mode in ('timeout', 'artifact'):
        folder=out/mode; folder.mkdir()
        child="import os,time,pathlib;os.setsid();time.sleep(2);pathlib.Path(%r).write_text('late')" % str(folder/'late')
        parent="import subprocess,time,sys,pathlib;subprocess.Popen([sys.executable,'-c',%r]);time.sleep(.4);pathlib.Path(%r).write_bytes(b'x'*20000);time.sleep(30)" % (child,str(folder/'fill'))
        events=[]
        result=execute([sys.executable,'-c',parent],folder,.8 if mode=='timeout' else 5,
                       100000 if mode=='timeout' else 10000,lambda kind,data: events.append({'event':kind,**data}))
        before=hashes(folder); time.sleep(2.1); after=hashes(folder)
        cases.append({'mode':mode,'result':result,'stable':before==after,'no_late_write':not (folder/'late').exists(),'events':events})
    folder=out/'compiler'; folder.mkdir(); events=[]
    result=execute(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(folder/'cache'),
                    str(ROOT/'tools/re/fixtures/AlphaReference.swift'),'-o',str(folder/'target')],
                   folder,60,16*1024*1024,lambda kind,data:events.append({'event':kind,**data}))
    snapshots=[hashes(folder)]
    for delay in (.2,1,2):
        time.sleep(delay); snapshots.append(hashes(folder))
    atomic(out/'cleanup-cases.json',cases)
    atomic(out/'compiler-quiescence.json',{'result':result,'events':events,'snapshots':snapshots})
    return {'detached_controls':2,'all_detached_stable':all(c['stable'] and c['no_late_write'] for c in cases),
            'timeout_observed':cases[0]['result']['execution']=='timed_out',
            'artifact_limit_observed':cases[1]['result']['execution']=='artifact_limit',
            'compiler_artifact_limit_observed':result['execution']=='artifact_limit',
            'compiler_cache_stable':all(s==snapshots[0] for s in snapshots),
            'scope':'Observed owned descendants stopped, cache snapshots stable through3.2s after return. Finite observation does not prove all arbitrary detached children or kernel quiescence.'}
