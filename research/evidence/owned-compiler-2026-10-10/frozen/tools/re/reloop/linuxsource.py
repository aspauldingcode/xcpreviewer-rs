"""Pinned source-derived WASM on an existing Linux VM; owned offline-container cleanup."""
import os
import pathlib
import subprocess
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.linuxwasm import verify_runtime,cleanup_owned,IMAGE,WHEEL
RUN="20261010T191804Z-portable-primary-source-subset-811cf568"
ANCHOR="45f7ac0b391eb74b2580209a237e231ee77d55be31c2857129c14137d69b3f88"

from reloop.verification import bytes_equal



def inspect(out,source,result):
    from reloop.primarysource import expected,validate,parse
    if result.get('host_system')!='Linux' or result.get('architecture')!='aarch64' or result.get('wasmtime')!='49.0.0':raise ValueError('Linux source host mismatch')
    for key,value in (('imports',0),('fuel_per_call',10000000),('memory_limit_bytes',131072)):
        if type(result.get(key)) is not int or result[key]!=value:raise ValueError('Linux source bounds/import mismatch')
    jobs=load(source/'jobs.json');checkers=load(source/'wasmkit.json')
    if len(jobs)!=16 or len(checkers)!=16:raise ValueError('Anchored source inventory')
    frames=result.get('frames');invalid=result.get('invalid');controls=result.get('controls');aggregates=result.get('aggregates');checker_invalid=result.get('checker_invalid')
    for rows,n in ((frames,64),(invalid,64),(controls,160),(aggregates,16),(checker_invalid,64)):
        if type(rows) is not list or len(rows)!=n:raise ValueError('Linux source result inventory')
        if any(type(row) is not dict for row in rows):raise ValueError('Linux source record shape')
    if result.get('renderer_hashes')!=[j['module_sha256'] for j in jobs]:raise ValueError('Linux source module identity')
    comparisons=[];cross=[];native=[];negatives=[];checker_negatives=[]
    wanted_frames=[];wanted_invalid=[];wanted_controls=[];wanted_aggregates=[];wanted_checker_invalid=[]
    for i,job in enumerate(jobs):
        validate(job['config'])
        if type(job['index']) is not int or job['index']!=i or job['strides']!=[job['config']['width']*4,min(256,job['config']['width']*4+12)] or any(type(s) is not int for s in job['strides']):raise ValueError('Anchored source configuration')
        if digest(source/('source-%d.wasm'%i))!=job['module_sha256'] or digest(source/('checker-%d.wasm'%i))!=checkers[i]['module_sha256']:raise ValueError('Anchored source module hash')
        if parse((source/('source-%d.swift'%i)).read_text())!=job['config'] or digest(source/('source-%d.ll'%i))!=job['ir_sha256']:raise ValueError('Anchored source/IR identity')
        for s,stride in enumerate(job['strides']):
            prediction=expected(job['config'],stride)
            if (source/('expected-%d-%d.raw'%(i,s))).read_bytes()!=prediction:raise ValueError('Independent source expectation changed')
            for repeat in range(2):
                path=out/('frame-%d-%d-%d.raw'%(i,s,repeat))
                wanted_frames.append({'job':i,'stride_index':s,'repeat':repeat,'bytes':16384,'sha256':digest(path)})
                comparisons.append(bytes_equal(source/('expected-%d-%d.raw'%(i,s)),path))
                cross.append(bytes_equal(source/('frame-%d-%d-%d.raw'%(i,s,repeat)),path))
                if (job['config']['width'],job['config']['height'],stride)==(17,9,80):native.append(bytes_equal(source/('native-%d-%d-%d.raw'%(i,s,repeat)),path))
        for k,stride in enumerate((0,job['config']['width']*4-1,257,0xffffffff)):
            wanted_invalid.append({'job':i,'index':k,'stride':stride})
            negatives.append(bytes_equal(source/('expected-%d-0.raw'%i),out/('invalid-%d-%d.raw'%(i,k))))
        reference=load(source/('checker-v8-%d.json'%i))
        wanted=[{'stride_index':s,'mutation':m,'count':1 if m else 0} for s in range(2) for m in range(5)]
        if reference!=wanted:raise ValueError('Anchored V8 checker result mismatch')
        wanted_controls.extend({'job':i,**row} for row in wanted)
        wanted_aggregates.append({'job':i,'count':8,'module_sha256':checkers[i]['module_sha256']})
        for k,(s,m) in enumerate(((2,0),(0,5),(0xffffffff,0),(0,0xffffffff))):
            baseline=out/('checker-baseline-%d.raw'%i)
            if baseline.stat().st_size!=131072:raise ValueError('Checker baseline extent')
            wanted_checker_invalid.append({'job':i,'index':k,'stride_index':s,'mutation':m,'count':0xffffffff,'baseline_sha256':digest(baseline),'bytes':131072})
            checker_negatives.append(bytes_equal(baseline,out/('checker-invalid-%d-%d.raw'%(i,k))))
    for rows,keys in ((frames,('job','stride_index','repeat','bytes')),(invalid,('job','index','stride')),(controls,('job','stride_index','mutation','count')),(aggregates,('job','count')),(checker_invalid,('job','index','stride_index','mutation','count','bytes'))):
        if any(any(type(row.get(k)) is not int for k in keys) for row in rows):raise ValueError('Linux source integer metadata')
    if frames!=wanted_frames or invalid!=wanted_invalid or controls!=wanted_controls or aggregates!=wanted_aggregates or checker_invalid!=wanted_checker_invalid:raise ValueError('Linux source record disagreement')
    if len(native)!=28 or not all(row['passed'] for row in comparisons+cross+native+negatives+checker_negatives):raise ValueError('Linux source exact allocation mismatch')
    atomic(out/'host-comparisons.json',{'independent':comparisons,'macos':cross,'native':native,'invalid':negatives,'checker_invalid':checker_negatives})
    return {'source_modules':16,'frames':64,'allocation_bytes':1048576,'cross_host_bytes':1048576,'native_full_bytes':len(native)*16384,'native_target_bytes':len(native)*720,'invalid_requests':64,'invalid_bytes':64*16384,'checker_controls':160,'mutation_controls':128,'aggregate_controls':16,'invalid_checker_requests':64,'invalid_checker_bytes':8388608,'imports':0,'host_system':'Linux','architecture':result['architecture'],'kernel':result['kernel'],'runtime':'Wasmtime49.0.0'}


def corpus(out):
    out=pathlib.Path(out);anchor=Controller(root=PROJECT_ROOT).verify(RUN,ANCHOR)
    if not anchor.get('valid') or not anchor.get('external_anchor_matches'):raise ValueError('Source anchor mismatch')
    atomic(out/'source-anchor.json',anchor);source=PROJECT_ROOT/'research/runs'/RUN/'output'
    staging=PROJECT_ROOT/'research/build/linux-wasmtime';verify_runtime(staging)
    owner=uuid.uuid4().hex;name='xcpreviewer-source-'+owner[:12]
    before=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    command=['docker','run','--rm','--pull','never','--name',name,'--label','xcpreviewer.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','%d:%d'%(os.getuid(),os.getgid()),'--env','PYTHONPATH=/runtime','--env','PYTHONDONTWRITEBYTECODE=1',
             '--mount','type=bind,src=%s,dst=/evidence,readonly'%source,'--mount','type=bind,src=%s,dst=/runtime,readonly'%(staging/'package'),'--mount','type=bind,src=%s,dst=/runner.py,readonly'%(ROOT/'tools/re/reloop/linux_source_runner.py'),'--mount','type=bind,src=%s,dst=/out'%out,'--entrypoint','/app/.venv/bin/python3',IMAGE,'-B','/runner.py']
    try:
        with (out/'linux.stdout').open('wb') as stdout,(out/'linux.stderr').open('wb') as stderr:
            subprocess.run(command,stdout=stdout,stderr=stderr,check=True,timeout=45)
    finally:cleanup_owned(name,owner,out)
    after=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    atomic(out/'existing-containers.json',{'before':before,'after':after,'existing_preserved':set(before)<=set(after)})
    if not set(before)<=set(after):raise ValueError('Existing container inventory changed during source control')
    result=inspect(out,source,load(out/'linux-source.json'))
    atomic(out/'runtime-identity.json',{'image':IMAGE,'wheel_sha256':WHEEL,'wheel_identity':load(staging/'identity.json')})
    return {**result,'owned_cleanup_verified':True,'existing_containers_preserved':True,'scope':'Actual Linux ARM64 Wasmtime execution of pinned source-derived standalone/checker modules, complete independent/native-prefix allocations, no-write invalid strides and exact checker fault counts. Frontend and LLVM compilation remain macOS; native getter/PNG differs. No Linux Swift frontend, browser/Windows, independent non-Apple hardware or native Canvas transport claim.'}
