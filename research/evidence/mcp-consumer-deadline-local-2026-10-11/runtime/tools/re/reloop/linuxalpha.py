"""Pinned alpha module on an existing Linux VM, with owned offline-container cleanup."""
import os
import pathlib
import subprocess
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.linuxwasm import verify_runtime,cleanup_owned,IMAGE,WHEEL
from reloop.browseralpha import RUN,ANCHOR
from reloop.portablealpha import CASES
from reloop.verification import bytes_equal


def inspect(out,source,result):
    if result.get('host_system')!='Linux' or result.get('architecture')!='aarch64' or result.get('wasmtime')!='49.0.0':raise ValueError('Linux alpha host mismatch')
    if type(result.get('imports')) is not int or result['imports']!=0:raise ValueError('Linux alpha imports')
    frames=result.get('frames');controls=result.get('checker_rows')
    if not isinstance(frames,list) or len(frames)!=108 or not isinstance(controls,list) or len(controls)!=32:raise ValueError('Linux alpha inventory')
    identities=load(source/'identities.json')
    for key,reference in [('renderer_module_sha256','renderer_module'),('checker_module_sha256','checker_module')]:
        if result.get(key)!=identities[reference]:raise ValueError('Linux alpha module identity')
    comparisons=[];cross=[];native=[]
    for i,job in enumerate(load(source/'execution.json')['rows']):
        if type(frames[i].get('index')) is not int or frames[i]['index']!=i or type(frames[i].get('bytes')) is not int or frames[i]['bytes']!=16384:raise ValueError('Linux alpha frame metadata')
        actual=out/('frame-%d.rgba'%i)
        if digest(actual)!=frames[i].get('sha256'):raise ValueError('Linux alpha payload hash')
        comparisons.append(bytes_equal(source/('expected-%d.rgba'%i),actual));cross.append(bytes_equal(source/('frame-%d.rgba'%i),actual))
        if (job['n'],job['bg']) in CASES and (job['w'],job['h'],job['stride'])==(17,9,68):
            active=out/('active-%d.rgba'%i);active.write_bytes(actual.read_bytes()[:612])
            native.append(bytes_equal(source/('native-%d.rgba'%CASES.index((job['n'],job['bg']))),active))
    if type(result.get('invalid_requests')) is not int or result['invalid_requests']!=12:raise ValueError('Linux alpha invalid inventory')
    invalid=[bytes_equal(source/'invalid-expected.rgba',out/('invalid-%d.rgba'%i)) for i in range(12)]
    if any(any(type(row.get(k)) is not int for k in ('variant','mutation','mismatches')) or row.get('passed') is not True for row in controls):raise ValueError('Linux alpha checker metadata')
    if controls!=load(source/'wasmkit.json'):raise ValueError('Linux/Wasmtime alpha checker disagreement')
    if not all(row['passed'] for row in comparisons+cross+native+invalid):raise ValueError('Linux alpha exact byte mismatch')
    atomic(out/'host-comparisons.json',{'independent':comparisons,'macos':cross,'native':native,'invalid':invalid})
    return {'frames':108,'allocation_bytes':sum(r['reference_bytes'] for r in comparisons),'cross_host_bytes':sum(r['reference_bytes'] for r in cross),'native_bytes':sum(r['reference_bytes'] for r in native),'invalid_requests':12,'invalid_bytes':sum(r['reference_bytes'] for r in invalid),'checker_controls':32,'mutation_controls':24,'imports':0,'host_system':'Linux','architecture':result['architecture'],'kernel':result['kernel'],'runtime':'Wasmtime49.0.0'}


def corpus(out):
    out=pathlib.Path(out);anchor=Controller(root=PROJECT_ROOT).verify(RUN,ANCHOR)
    if not anchor['valid']:raise ValueError('Alpha source anchor mismatch')
    atomic(out/'source-anchor.json',anchor);source=PROJECT_ROOT/'research/runs'/RUN/'output'
    staging=PROJECT_ROOT/'research/build/linux-wasmtime';verify_runtime(staging)
    owner=uuid.uuid4().hex;name='xcpreviewer-alpha-'+owner[:12]
    before=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    command=['docker','run','--rm','--pull','never','--name',name,'--label','xcpreviewer.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','%d:%d'%(os.getuid(),os.getgid()),'--env','PYTHONPATH=/runtime','--env','PYTHONDONTWRITEBYTECODE=1',
             '--mount','type=bind,src=%s,dst=/evidence,readonly'%source,'--mount','type=bind,src=%s,dst=/runtime,readonly'%(staging/'package'),'--mount','type=bind,src=%s,dst=/runner.py,readonly'%(ROOT/'tools/re/reloop/linux_alpha_runner.py'),'--mount','type=bind,src=%s,dst=/out'%out,'--entrypoint','/app/.venv/bin/python3',IMAGE,'-B','/runner.py']
    try:
        with (out/'linux.stdout').open('wb') as stdout,(out/'linux.stderr').open('wb') as stderr:
            subprocess.run(command,stdout=stdout,stderr=stderr,check=True,timeout=45)
    finally:cleanup_owned(name,owner,out)
    after=subprocess.run(['docker','ps','--format','{{.ID}} {{.Names}}'],capture_output=True,text=True,check=True,timeout=8).stdout.splitlines()
    atomic(out/'existing-containers.json',{'before':before,'after':after,'existing_preserved':set(before)<=set(after)})
    if not set(before)<=set(after):raise ValueError('Existing container inventory changed during alpha control')
    result=inspect(out,source,load(out/'linux-alpha.json'))
    atomic(out/'runtime-identity.json',{'image':IMAGE,'wheel_sha256':WHEEL,'wheel_identity':load(staging/'identity.json')})
    return {**result,'owned_cleanup_verified':True,'existing_containers_preserved':True,'scope':'Exact pinned alpha WASM on Linux ARM64 in existing Colima VM/Apple hardware, full native/model/padding/tail allocations. macOS compilation retained. No Linux source frontend, independent non-Apple hardware, Windows, Canvas wire or cost claim.'}
