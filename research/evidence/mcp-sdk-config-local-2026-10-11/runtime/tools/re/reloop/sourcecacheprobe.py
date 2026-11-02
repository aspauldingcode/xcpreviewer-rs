"""Owned CLI/cache transaction controls versus independently anchored source modules."""
import pathlib
import subprocess
import sys
from reloop.core import ROOT,PROJECT_ROOT,Controller,load,atomic,digest
from reloop.portable import TOOLCHAIN
from reloop.primarysource import expression,expected
from reloop.sourcecache import build
from reloop.browsersource import RUN,ANCHOR
from reloop.verification import bytes_equal


def corpus(out):
    out=pathlib.Path(out);v=Controller(root=PROJECT_ROOT).verify(RUN,ANCHOR)
    if not v['valid'] or not v['external_anchor_matches']:raise ValueError('CLI source anchor mismatch')
    atomic(out/'source-anchor.json',v);source=PROJECT_ROOT/'research/runs'/RUN/'output';refs=load(source/'jobs.json')
    cache=out/'cache';published=out/'published';input_path=out/'input.swift';receipts=[];calls=[]
    def cli(text,tool=TOOLCHAIN/'clang',success=True,linker=TOOLCHAIN/'wasm-ld'):
        input_path.write_text(text)
        args=[sys.executable,ROOT/'tools/re/source_cli.py',input_path,'--cache',cache,'--output',published,'--clang',tool,'--wasm-ld',linker]
        r=subprocess.run([str(a) for a in args],capture_output=True,timeout=75)
        index=len(calls);calls.append({'call':index,'exit_code':r.returncode,'expected_success':success})
        (out/('cli-%d.stdout'%index)).write_bytes(r.stdout);(out/('cli-%d.stderr'%index)).write_bytes(r.stderr);atomic(out/'cli-calls.json',calls)
        if (r.returncode==0)!=success:raise ValueError('Owned CLI exit mismatch')
        import json
        row=json.loads(r.stdout if success else r.stderr)
        if row['ok']!=success:raise ValueError('Owned CLI result mismatch')
        return row
    text=expression(4);texts=[text,text,text.replace('Color(', 'Color ('),expression(4,1)];jobs=[];module_equal=[];ir_equal=[]
    for i,text in enumerate(texts):
        receipt=cli(text);receipts.append(receipt)
        if receipt['cache_hit']!=(i in (1,2)):raise ValueError('CLI cache-hit contract')
        reference=refs[1 if i==3 else 0];folder=published/'versions'/receipt['entry_sha256'];module_equal.append(bytes_equal(source/('source-%d.wasm'%reference['index']),folder/'view.wasm'));ir_equal.append(bytes_equal(source/('source-%d.ll'%reference['index']),folder/'view.ll'))
        jobs.append({'index':i,'config':receipt['config'],'strides':reference['strides'],'module':str(folder/'view.wasm')})
    if receipts[0]['source_sha256']==receipts[2]['source_sha256'] or receipts[0]['cache_key']!=receipts[2]['cache_key'] or receipts[0]['cache_key']==receipts[3]['cache_key']:raise ValueError('Source provenance/semantic cache key mismatch')
    if not all(r['passed'] for r in module_equal+ir_equal):raise ValueError('CLI module/IR differs from anchored compiler output')
    atomic(out/'receipts.json',receipts);atomic(out/'jobs.json',jobs)
    r=subprocess.run(['node',str(ROOT/'tools/re/reloop/primary_source_runner.js'),str(out)],capture_output=True,timeout=30)
    (out/'node.stdout').write_bytes(r.stdout);(out/'node.stderr').write_bytes(r.stderr)
    if r.returncode:raise ValueError('Owned CLI module execution failed')
    frames=[];native=[];invalid=[]
    for job in jobs:
        i=job['index'];reference=refs[1 if i==3 else 0]
        for s,stride in enumerate(job['strides']):
            prediction=out/('expected-%d-%d.raw'%(i,s));prediction.write_bytes(expected(job['config'],stride))
            for repeat in range(2):
                actual=out/('frame-%d-%d-%d.raw'%(i,s,repeat));frames.append(bytes_equal(prediction,actual))
                if stride==80:native.append(bytes_equal(source/('native-%d-%d-%d.raw'%(reference['index'],s,repeat)),actual))
        invalid.extend(bytes_equal(out/('expected-%d-0.raw'%i),out/('invalid-%d-%d.raw'%(i,k))) for k in range(4))
    if not all(r['passed'] for r in frames+native+invalid):raise ValueError('CLI independent/native/no-write bytes mismatch')
    pointer=published/'current.json';before=pointer.read_bytes();controls=[];last=receipts[-1];folder=cache/'entries'/last['entry_sha256'];index=cache/'keys'/(last['cache_key']+'.json')
    def preserved(name):
        same=pointer.read_bytes()==before
        if not same:raise ValueError('Failed CLI build replaced last valid pointer')
        controls.append({'control':name,'pointer_unchanged':same,'published_module_sha256':digest(published/last['module'])})
    cli('Text("unsupported")',success=False);preserved('unsupported-source')
    for name in ('view.wasm','manifest.json'):
        path=folder/name;raw=path.read_bytes();path.write_bytes(raw+b'bad')
        try:cli(texts[3],success=False);preserved('corrupt-'+name)
        finally:path.write_bytes(raw)
    raw=index.read_bytes();atomic(index,{'version':1,'entry_sha256':'../escape'})
    try:cli(texts[3],success=False);preserved('invalid-cache-index')
    finally:index.write_bytes(raw)
    cli(texts[3],tool=pathlib.Path('/usr/bin/false'),success=False);preserved('compiler-failure')
    alias_failure=cli(texts[3],success=False,linker=(TOOLCHAIN/'wasm-ld').resolve())
    if 'generic driver' not in alias_failure.get('error',''):raise ValueError('Named linker flavor control failed')
    preserved('generic-linker-alias')
    try:build(texts[3],cache,published,TOOLCHAIN/'clang',TOOLCHAIN/'wasm-ld',fault_before_commit=True)
    except RuntimeError as error:
        if str(error)!='Owned pre-publication fault':raise
        preserved('pre-publication-fault')
    else:raise ValueError('Owned pre-publication fault absent')
    if any(c['published_module_sha256']!=last['module_sha256'] for c in controls):raise ValueError('Published module changed after failed build')
    if list(cache.glob('.owned-build-*')) or list(published.glob('.owned-publish-*')):raise ValueError('Owned staging cleanup incomplete')
    atomic(out/'comparisons.json',{'module':module_equal,'ir':ir_equal,'independent':frames,'native':native,'invalid':invalid});atomic(out/'failure-controls.json',controls)
    return {'cli_builds':4,'cache_hits':2,'module_equal':True,'ir_equal':True,'source_provenance_distinct':True,'semantic_cache_shared':True,'changed_source_key_distinct':True,'frames':16,'allocation_bytes':262144,'native_target_bytes':len(native)*720,'invalid_requests':16,'invalid_bytes':262144,'failure_controls':7,'all_failed_builds_preserve_pointer':True,'staging_cleanup':True,'scope':'Owned primary-layer source CLI, semantic identity cache and atomic single published-bundle pointer; exact compiler output and full native/model/no-write bytes. macOS compilation/V8 only. Local integrity is not authentication; no active runtime swap, state preservation, stale generation, watch/debounce, native Canvas or general SwiftUI acceptance.'}
