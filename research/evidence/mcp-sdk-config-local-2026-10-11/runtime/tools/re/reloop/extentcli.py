"""Frozen supported source-frame CLI versus full public native extent references.

PNG is independently decoded against a declared straight-alpha projection; it is
not compared to native getter/PNG bytes. No browser or current mutable CLI used.
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from fractions import Fraction
from PIL import Image
from reloop.core import Controller,ROOT,PROJECT_ROOT,atomic,digest,load
from reloop.primarysource import expression,parse,expected
from reloop.verification import bytes_equal

NATIVE_RUN='20261010T215252Z-native-primary-extent-holdouts-5143e5b4'
NATIVE_ANCHOR='5786fc404ec0181161d42e431b303425260af6adb3d517bf92351cbf542301fa'
CLI_RUN='20261010T215404Z-primary-source-frame-cli-8a8fd3bc'
CLI_ANCHOR='9dba73bc8a5098d92441a4bd5e34ada36548f2cbb51387ba2844b6d008cdd4ac'


def project_rgba(raw,config,stride):
    """Independent Fraction projection, excluding row padding and unused tail."""
    if len(raw)!=16384:raise ValueError('Full allocation required')
    pixels=bytearray()
    for y in range(config['height']):
        for x in range(config['width']):
            p=raw[y*stride+x*4:y*stride+x*4+4];alpha=p[3]
            pixels.extend(0 if alpha==0 else int(Fraction(c*255,alpha)+Fraction(1,2)) for c in p[:3]);pixels.append(alpha)
    return bytes(pixels)


def check_png(path,config,predicted):
    with Image.open(path) as image:
        image.load()
        if image.size!=(config['width'],config['height']) or image.mode!='RGBA' or type(image.info.get('srgb')) is not int or image.info['srgb']!=0:raise ValueError('PNG dimensions/mode/sRGB mismatch')
        raw=image.tobytes()
    return {'bytes':len(raw),'passed':raw==predicted,'sha256':hashlib.sha256(raw).hexdigest()}


def corpus(out):
    controller=Controller(root=PROJECT_ROOT);pins=[]
    for rid,anchor in ((NATIVE_RUN,NATIVE_ANCHOR),(CLI_RUN,CLI_ANCHOR)):
        v=controller.verify(rid,anchor)
        if not v['valid'] or not v['external_anchor_matches']:raise ValueError('Extent CLI prerequisite anchor mismatch')
        pins.append(v)
    atomic(out/'anchors.json',pins)
    native=PROJECT_ROOT/'research/runs'/NATIVE_RUN/'output'
    frozen=PROJECT_ROOT/'research/runs'/CLI_RUN/'source/tools/re'
    cli_path=frozen/'preview_cli.py'
    # Use the already sealed executable/tool paths, preserving named linker flavor.
    prior=load(PROJECT_ROOT/'research/runs'/CLI_RUN/'output/receipts.json')[0]
    prior_manifest=load(PROJECT_ROOT/'research/runs'/CLI_RUN/'output/preview/versions'/prior['entry_sha256']/'manifest.json')
    compiler_entry=prior_manifest['identity']['compiler_entry']
    compiler=load(PROJECT_ROOT/'research/runs'/CLI_RUN/'output/cache/entries'/compiler_entry/'manifest.json')['identity']
    clang=pathlib.Path(compiler['clang_invocation']);linker=pathlib.Path(compiler['wasm_ld_invocation'])
    if digest(clang)!=compiler['clang_sha256'] or digest(linker)!=compiler['wasm_ld_sha256']:raise ValueError('Frozen compiler identity changed')
    node=pathlib.Path(shutil.which('node') or '').absolute()
    if not node.is_file() or digest(node)!=prior_manifest['identity']['runtime_sha256']:raise ValueError('Frozen runtime identity changed')
    jobs=load(native/'predictions.json')['jobs']
    # Validate the full extent denominator independently of native result files.
    expected_jobs=[]
    for case in (4,8,18,19):
        for reverse in (0,1):
            for width,height,stride in ((1,1,4),(1,1,16),(13,7,52),(13,7,64),(64,64,256)):
                expected_jobs.append({'index':len(expected_jobs),'case':case,'order':'reverse' if reverse else 'forward','config':parse(expression(case,reverse,width,height)),'stride':stride})
    if json.dumps(jobs,sort_keys=True)!=json.dumps(expected_jobs,sort_keys=True):raise ValueError('Native extent denominator changed')
    jobs=jobs+[{'index':40+i,'case':3,'order':'forward','config':parse(expression(3,0,w,h)),'stride':s,'independent_only':True} for i,(w,h,s) in enumerate(((1,1,4),(13,7,64)))]
    atomic(out/'jobs.json',jobs)
    cache=out/'cache';published=out/'published';source=out/'input.swift';calls=[];receipts=[];frames=[];native_rows=[];png_rows=[]
    def cli(text,stride,success=True,runtime=node,seconds=5):
        source.write_text(text);i=len(calls)
        args=[sys.executable,cli_path,source,'--cache',cache,'--output',published,'--clang',clang,'--wasm-ld',linker,'--node',runtime,'--stride',str(stride),'--runtime-seconds',str(seconds)]
        r=subprocess.run([str(a) for a in args],capture_output=True,timeout=75)
        (out/('cli-%d.stdout'%i)).write_bytes(r.stdout);(out/('cli-%d.stderr'%i)).write_bytes(r.stderr)
        calls.append({'index':i,'exit_code':r.returncode,'expected_success':success});atomic(out/'calls.json',calls)
        row=json.loads(r.stdout)
        if type(row.get('ok')) is not bool or row['ok']!=success or (r.returncode==0)!=success:raise ValueError('Frozen CLI exit/result mismatch')
        return row
    for job in jobs:
        c=job['config'];stride=job['stride'];i=job['index'];text=expression(job['case'],c['reverse'],c['width'],c['height'])
        prediction=out/('expected-%d.raw'%i);prediction.write_bytes(expected(c,stride))
        projected=project_rgba(prediction.read_bytes(),c,stride);(out/('expected-%d.rgba'%i)).write_bytes(projected)
        for repeat in range(2):
            receipt=cli(text,stride);receipts.append(receipt)
            if receipt['config']!=c or type(receipt['stride']) is not int or receipt['stride']!=stride or receipt['source_sha256']!=hashlib.sha256(text.encode()).hexdigest():raise ValueError('Frozen CLI source/configuration mismatch')
            folder=published/'versions'/receipt['entry_sha256'];actual=out/('frame-%d-%d.raw'%(i,repeat));shutil.copyfile(folder/'allocation.raw',actual)
            frames.append(bytes_equal(prediction,actual))
            if not job.get('independent_only'):native_rows.append(bytes_equal(native/('native-%d-%d.raw'%(i,repeat)),actual))
            png=out/('preview-%d-%d.png'%(i,repeat));shutil.copyfile(folder/'preview.png',png);png_rows.append(check_png(png,c,projected))
            if digest(folder/'view.wasm')!=receipt['module_sha256'] or digest(actual)!=receipt['allocation_sha256'] or digest(png)!=receipt['png_sha256']:raise ValueError('Frozen CLI receipt payload mismatch')
    if not all(r['passed'] for r in frames+native_rows+png_rows):raise ValueError('Full native/independent/PNG extent mismatch')
    atomic(out/'receipts.json',receipts);atomic(out/'comparisons.json',{'independent':frames,'native':native_rows,'png':png_rows})
    # Falsify the independent verifier at pixel, padding and final tail offsets.
    controls=[];reference=out/'expected-3.raw'
    for name,offset in (('pixel',0),('padding',52),('tail',16383)):
        raw=bytearray(reference.read_bytes());raw[offset]^=1;path=out/('mutant-'+name+'.raw');path.write_bytes(raw)
        r=bytes_equal(reference,path)
        if r['passed'] or r['different_bytes']!=1 or r['different_bits_in_shared_extent']!=1:raise ValueError('Extent byte corruption escaped verifier')
        controls.append({'control':name,'comparison':r})
    # A valid encoded PNG with changed alpha must also fail the independent pixel gate.
    with Image.open(out/'preview-3-0.png') as original:
        image=original.copy();pixel=list(image.getpixel((0,0)));pixel[3]^=1;image.putpixel((0,0),tuple(pixel))
        from PIL.PngImagePlugin import PngInfo
        info=PngInfo();info.add(b'sRGB',b'\0');image.save(out/'mutant-alpha.png',pnginfo=info)
    bad=check_png(out/'mutant-alpha.png',jobs[3]['config'],project_rgba(reference.read_bytes(),jobs[3]['config'],jobs[3]['stride']))
    if bad['passed']:raise ValueError('PNG alpha corruption escaped verifier')
    controls.append({'control':'png-alpha','comparison':bad});atomic(out/'verifier-controls.json',controls)
    pointer=published/'current.json';before=pointer.read_bytes();last=load(pointer)
    baseline={name:digest(published/last[name]) for name in ('allocation','png')};failures=[]
    def preserved(name):
        if pointer.read_bytes()!=before or any(digest(published/last[k])!=v for k,v in baseline.items()):raise ValueError('Failed extent preview replaced last valid output')
        failures.append({'control':name,'pointer_unchanged':True,'payload_hashes':baseline})
    text=expression(4,0,13,7)
    cli('Text("unsupported")',52,False);preserved('unsupported-source')
    cli(text,51,False);preserved('invalid-stride')
    cli(text,52,False,pathlib.Path('/usr/bin/false'));preserved('runtime-exit')
    cli(text,52,False,pathlib.Path('/usr/bin/true'));preserved('runtime-missing-output')
    sleeper=out/'owned-timeout';sleeper.write_text('#!/bin/sh\nexec /bin/sleep 2\n');sleeper.chmod(0o700)
    cli(text,52,False,sleeper,0.1);preserved('runtime-timeout')
    compiler_entry=load(published/'versions'/receipts[4]['entry_sha256']/'manifest.json')['identity']['compiler_entry']
    for name in ('view.wasm','manifest.json'):
        path=cache/'entries'/compiler_entry/name;raw=path.read_bytes();path.write_bytes(raw+b'bad')
        try:cli(text,52,False);preserved('corrupt-cache-'+name)
        finally:path.write_bytes(raw)
    # Fault within a frozen adapter via a small owned subprocess, not mutable imports.
    fault=out/'owned-precommit.py';fault.write_text("import sys\nsys.path.insert(0,sys.argv[1])\nfrom reloop.sourceframe import render\nfrom pathlib import Path\nrender(Path(sys.argv[2]).read_text(),*[Path(x) for x in sys.argv[3:8]],stride=52,fault_before_commit=True)\n")
    source.write_text(text)
    r=subprocess.run([sys.executable,str(fault),str(frozen),str(source),str(cache),str(published),str(clang),str(linker),str(node)],capture_output=True,timeout=75)
    (out/'precommit.stdout').write_bytes(r.stdout);(out/'precommit.stderr').write_bytes(r.stderr)
    if not r.returncode or b'Owned frame pre-publication fault' not in r.stderr:raise ValueError('Missing frozen precommit fault')
    preserved('pre-publication-fault')
    if list(published.glob('.owned-frame-*')) or list(cache.glob('.owned-build-*')):raise ValueError('Extent CLI staging cleanup incomplete')
    atomic(out/'failure-controls.json',failures)
    return {'native_jobs':40,'frames':84,'allocation_bytes':84*16384,'native_frames':80,'native_full_bytes':80*16384,'native_padding_bytes':1536,'native_tail_bytes':1035264,'independent_matches':sum(r['passed'] for r in frames),'native_matches':sum(r['passed'] for r in native_rows),'pngs':len(png_rows),'png_decoded_bytes':sum(r['bytes'] for r in png_rows),'png_matches':sum(r['passed'] for r in png_rows),'transparent_frames':4,'verifier_faults':len(controls),'failure_controls':len(failures),'last_good_preserved':True,'staging_cleanup':True,'scope':'Pinned frozen source-frame CLI, macOS LLVM compilation and V8.80 complete public native extent allocations plus4 independently predicted transparent frames; Fraction-projected PNG decoded independently. No native PNG/getter equivalence, current mutable CLI assurance, browser, hot reload/state migration, general SwiftUI or Canvas protocol acceptance.'}
