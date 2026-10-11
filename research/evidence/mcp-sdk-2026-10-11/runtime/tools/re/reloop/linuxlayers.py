"""Pinned alpha module on an existing Linux VM, with owned offline-container cleanup."""
import os
import pathlib
import subprocess
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.linuxwasm import verify_runtime,cleanup_owned,IMAGE,WHEEL
from reloop.portablelayers import PORTABLE_RUN as RUN,PORTABLE_ANCHOR as ANCHOR

from reloop.verification import bytes_equal


def inspect(out,source,result):
    if result.get('host_system')!='Linux' or result.get('architecture')!='aarch64' or result.get('wasmtime')!='49.0.0':raise ValueError('Linux layer host mismatch')
    if type(result.get('imports')) is not int or result['imports']!=0:raise ValueError('Linux layer imports')
    frames=result.get('frames');controls=result.get('checker_rows')
    if not isinstance(frames,list) or len(frames)!=320 or not isinstance(controls,list) or len(controls)!=200:raise ValueError('Linux layer inventory')
    identities=load(source/'identities.json')
    for key,reference in [('renderer_module_sha256','renderer_module'),('checker_module_sha256','checker_module')]:
        if result.get(key)!=identities[reference]:raise ValueError('Linux layer module identity')
    if result.get('fuel_per_call')!=10000000 or type(result.get('fuel_per_call')) is not int or result.get('memory_limit_bytes')!=131072 or type(result.get('memory_limit_bytes')) is not int:raise ValueError('Linux layer runtime bounds')
    jobs=load(source/'execution.json')['rows']
    if len(jobs)!=320:raise ValueError('Anchored layer input inventory')
    comparisons=[];cross=[];native=[]
    for i,job in enumerate(jobs):
        if type(frames[i].get('index')) is not int or frames[i]['index']!=i or type(frames[i].get('bytes')) is not int or frames[i]['bytes']!=16384:raise ValueError('Linux layer frame metadata')
        actual=out/('frame-%d.raw'%i)
        if digest(actual)!=frames[i].get('sha256'):raise ValueError('Linux layer payload hash')
        comparisons.append(bytes_equal(source/('expected-%d.raw'%i),actual));cross.append(bytes_equal(source/('frame-%d.raw'%i),actual))
        if (job['w'],job['h'],job['stride'])==(17,9,80):native.append(bytes_equal(source/('native-full-%d.raw'%i),actual))
    if type(result.get('invalid_requests')) is not int or result['invalid_requests']!=17:raise ValueError('Linux layer invalid inventory')
    invalid=[bytes_equal(source/'invalid-expected.raw',out/('invalid-%d.raw'%i)) for i in range(17)]
    if any(any(type(row.get(k)) is not int for k in ('variant','mutation','count')) for row in controls):raise ValueError('Linux layer checker metadata')
    expected=[{'variant':v,'mutation':m,'count':1 if m else 0} for v in range(40) for m in range(5)]
    if controls!=expected or controls!=load(source/'checker-v8.json')['rows']:raise ValueError('Linux/native layer checker disagreement')
    if not all(row['passed'] for row in comparisons+cross+native+invalid):raise ValueError('Linux layer exact byte mismatch')
    atomic(out/'host-comparisons.json',{'independent':comparisons,'macos':cross,'native':native,'invalid':invalid})
    return {'frames':320,'allocation_bytes':sum(r['reference_bytes'] for r in comparisons),'cross_host_bytes':sum(r['reference_bytes'] for r in cross),'native_full_bytes':sum(r['reference_bytes'] for r in native),'native_target_bytes':len(native)*720,'invalid_requests':17,'invalid_bytes':sum(r['reference_bytes'] for r in invalid),'checker_controls':200,'mutation_controls':160,'imports':0,'host_system':'Linux','architecture':result['architecture'],'kernel':result['kernel'],'runtime':'Wasmtime49.0.0'}


MUTANT_RUN='20261010T185711Z-portable-primary-layer-algorithm-mutants-f18b9d9e'
MUTANT_ANCHOR='1158c7335125110c92030359b7c150a7545278beee638bf7207b5d4304d8facf'


def inspect_mutants(source,result):
    if result.get('host_system')!='Linux' or result.get('architecture')!='aarch64' or result.get('wasmtime')!='49.0.0':raise ValueError('Linux mutant host mismatch')
    for key,value in (('imports',0),('memory_limit_bytes',131072),('fuel_per_case',10000000),('fuel_per_aggregate',50000000)):
        if type(result.get(key)) is not int or result[key]!=value:raise ValueError('Linux mutant bounds/import mismatch')
    rows=result.get('mutants')
    if not isinstance(rows,list) or len(rows)!=2:raise ValueError('Linux mutant inventory')
    targets=load(source/'mutations.json')
    for row,expected in zip(rows,targets):
        if row.get('mutation')!=expected['mutation'] or row.get('module_sha256')!=expected['module_sha256']:raise ValueError('Linux mutant identity mismatch')
        controls=row.get('rows')
        if not isinstance(controls,list) or len(controls)!=40 or any(type(c.get('variant')) is not int or type(c.get('mismatches')) is not int for c in controls):raise ValueError('Linux mutant count metadata')
        if controls!=load(source/(expected['mutation']+'.json'))['rows']:raise ValueError('Linux semantic mutant disagreement')
        if type(row.get('aggregate')) is not int or row['aggregate']!=0xffffffff or type(row.get('witness')) is not int or row['witness']!=expected['v8_witness']:raise ValueError('Linux mutant rejection/witness mismatch')
    return {'algorithm_mutants':2,'native_cases':80,'all_detected':True,'all_cross_host_counts_equal':True,'host_system':'Linux','architecture':result['architecture'],'kernel':result['kernel'],'runtime':'Wasmtime49.0.0'}


def corpus(out,mutations=False):
    out=pathlib.Path(out);anchor=Controller(root=PROJECT_ROOT).verify(MUTANT_RUN if mutations else RUN,MUTANT_ANCHOR if mutations else ANCHOR)
    if not anchor.get('valid') or not anchor.get('external_anchor_matches'):raise ValueError('Layer source anchor mismatch')
    atomic(out/'source-anchor.json',anchor);source=PROJECT_ROOT/'research/runs'/(MUTANT_RUN if mutations else RUN)/'output'
    staging=PROJECT_ROOT/'research/build/linux-wasmtime';verify_runtime(staging)
    owner=uuid.uuid4().hex;name='xcpreviewer-layers-'+owner[:12]
    before=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    command=['docker','run','--rm','--pull','never','--name',name,'--label','xcpreviewer.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','%d:%d'%(os.getuid(),os.getgid()),'--env','PYTHONPATH=/runtime','--env','PYTHONDONTWRITEBYTECODE=1',
             '--mount','type=bind,src=%s,dst=/evidence,readonly'%source,'--mount','type=bind,src=%s,dst=/runtime,readonly'%(staging/'package'),'--mount','type=bind,src=%s,dst=/runner.py,readonly'%(ROOT/('tools/re/reloop/linux_layers_mutant_runner.py' if mutations else 'tools/re/reloop/linux_layers_runner.py')),'--mount','type=bind,src=%s,dst=/out'%out,'--entrypoint','/app/.venv/bin/python3',IMAGE,'-B','/runner.py']
    try:
        with (out/'linux.stdout').open('wb') as stdout,(out/'linux.stderr').open('wb') as stderr:
            subprocess.run(command,stdout=stdout,stderr=stderr,check=True,timeout=45)
    finally:cleanup_owned(name,owner,out)
    after=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    atomic(out/'existing-containers.json',{'before':before,'after':after,'existing_preserved':set(before)<=set(after)})
    if not set(before)<=set(after):raise ValueError('Existing container inventory changed during alpha control')
    result=inspect_mutants(source,load(out/'linux-layer-mutants.json')) if mutations else inspect(out,source,load(out/'linux-layers.json'))
    atomic(out/'runtime-identity.json',{'image':IMAGE,'wheel_sha256':WHEEL,'wheel_identity':load(staging/'identity.json')})
    return {**result,'owned_cleanup_verified':True,'existing_containers_preserved':True,'scope':'Actual Linux semantic algorithm mutants versus anchored full native checker; paired host case counts, no new native acquisition or raw mutant frame captures.' if mutations else 'Exact pinned primary-layer WASM on Linux ARM64 in existing Colima VM/Apple hardware, full native callback-target/model/padding/tail allocations; native getter/PNG differences retained. macOS compilation retained. No Linux source frontend, independent non-Apple hardware, Windows, Canvas wire or cost claim.'}
