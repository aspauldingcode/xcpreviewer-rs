"""Portable primary-layer callback-target feasibility; not native getter output."""
import subprocess
from reloop.core import ROOT,PROJECT_ROOT,Controller,atomic,digest,load
from reloop.portable import TOOLCHAIN
from reloop.primarylayers import CASES,EXTRA_CASES,pixel
from reloop.mixedcallback import inspect_metadata
from reloop.wasmkit import parse_result
from reloop.verification import bytes_equal

RUN='20261010T184640Z-native-primary-layer-holdouts-05e3ae4b'
ANCHOR='0dfae6bf400c8d511bd921027daa9f779d06596ffa177eb3a47cab5d1ae43b28'
CAPACITY=16384


def expected(w,h,stride,case,reverse):
    if any(type(v) is not int for v in (w,h,stride,case,reverse)) or not(1<=w<=64 and 1<=h<=64 and w*4<=stride<=256 and 0<=case<20 and reverse in (0,1)):raise ValueError('Unsupported portable layer request')
    active=pixel(case,'reverse' if reverse else 'forward','quantized-stage')*w
    raw=(active+bytes([165])*(stride-w*4))*h
    return raw+bytes([195])*(CAPACITY-len(raw))


def corpus(out):
    controller=Controller(root=PROJECT_ROOT);v=controller.verify(RUN,ANCHOR)
    if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Native layer oracle anchor changed')
    atomic(out/'native-anchor.json',v);atomic(out/'inputs.json',CASES+EXTRA_CASES)
    source=ROOT/'tools/re/fixtures/portable_layers.c';ir=out/'layers.ll';module=out/'layers.wasm';clang=TOOLCHAIN/'clang';linker=TOOLCHAIN/'wasm-ld'
    atomic(out/'predictions.json',{'native_run':RUN,'native_anchor':ANCHOR,'source_sha256':digest(source),'scope':'Primary-only premultiplied source-over callback-target contract; alpha eighths, order,RGBA8,paddinga5,tailc3. Independent Fraction predictions and native buffers separately compared; getter/PNG differences retained.'})
    def command(args,name):
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:subprocess.run([str(a) for a in args],stdout=stdout,stderr=stderr,check=True,timeout=30)
    command([clang,'--version'],'clang-version');command([clang,'--target=wasm32','-O2','-nostdlib','-fno-builtin','-emit-llvm','-S',source,'-o',ir],'emit-ir')
    flags=['--target=wasm32','-O2','-nostdlib','-fno-builtin','-fuse-ld='+str(linker),'-Wl,--no-entry','-Wl,--initial-memory=131072','-Wl,--max-memory=131072']
    command([clang,*flags,ir,'-Wl,--export=render','-Wl,--export=pixels','-Wl,--export=capacity','-o',module],'link')
    runner=ROOT/'tools/re/reloop/portable_layers_runner.js';command(['node',runner,module,out],'v8')
    execution=load(out/'execution.json');comparisons=[];native_checks=[];repeats=[];native=[]
    for case in range(20):
        for reverse,order in enumerate(('forward','reverse')):
            path=controller.runs/RUN/'output'/('layers-%d-%s-0.0.raw'%(case,order));raw=path.read_bytes();inspect_metadata(load(path.with_suffix('.json')),raw,0)
            native.append(raw);(out/('native-%d.raw'%(case*2+reverse))).write_bytes(raw)
    for row in execution['rows']:
        i=row['index'];pred=out/('expected-%d.raw'%i);pred.write_bytes(expected(row['w'],row['h'],row['stride'],row['variant'],row['reverse']));actual=out/('frame-%d.raw'%i);comparisons.append(bytes_equal(pred,actual))
        if row['repeat']==1:repeats.append(bytes_equal(out/('frame-%d.raw'%(i-1)),actual))
        if (row['w'],row['h'],row['stride'])==(17,9,80):
            target=out/('native-full-%d.raw'%i);target.write_bytes(native[row['variant']*2+row['reverse']]+bytes([195])*(CAPACITY-720));native_checks.append(bytes_equal(target,actual))
    invalid_pred=out/'invalid-expected.raw';invalid_pred.write_bytes(expected(17,9,80,4,0))
    baseline=bytes_equal(invalid_pred,out/'invalid-before.raw')
    if not baseline['passed']:raise ValueError('Layer invalid-request baseline differs from independent allocation')
    invalid=[bytes_equal(out/'invalid-before.raw',out/('invalid-%d.raw'%i)) for i in range(len(execution['invalid']))]
    atomic(out/'comparisons.json',{'allocations':comparisons,'native':native_checks,'repeats':repeats,'invalid':invalid})
    (out/'layer_expectations.h').write_text('static const unsigned source_alphas[20][3]={'+','.join('{'+','.join(map(str,a))+'}' for a in CASES+EXTRA_CASES)+'};\nstatic const unsigned char native_targets[40][720]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in native)+'};\n')
    checker=out/'layers-checker.wasm';command([clang,*flags,ir,ROOT/'tools/re/fixtures/portable_layers_verify.c','-I',out,'-Wl,--export=verify','-Wl,--export=verify_all','-o',checker],'checker-link');command(['node',runner,checker,out,'checker'],'checker-v8')
    rows=[]
    for mutation in range(5):
        name='wasmkit-%d'%mutation;command([TOOLCHAIN/'wasmkit','run',checker,'verify_all','i32:'+str(mutation)],name);count=parse_result((out/(name+'.stdout')).read_text());rows.append({'mutation':mutation,'count':count,'expected':40 if mutation else 0,'passed':count==(40 if mutation else 0),'per_case_expected_enforced':True})
    atomic(out/'wasmkit.json',rows);atomic(out/'identities.json',{'clang':digest(clang),'wasm_ld':digest(linker),'wasmkit':digest(TOOLCHAIN/'wasmkit'),'source':digest(source),'renderer_ir':digest(ir),'renderer_module':digest(module),'checker_module':digest(checker),'node':execution['node'],'v8':execution['v8']})
    return {'frames':len(comparisons),'allocation_bytes':len(comparisons)*CAPACITY,'all_allocations_equal':all(p['passed'] for p in comparisons),'native_frames':len(native_checks),'native_full_bytes':len(native_checks)*CAPACITY,'native_target_bytes':len(native_checks)*720,'all_native_equal':all(p['passed'] for p in native_checks),'repeat_pairs':len(repeats),'all_repeats_equal':all(p['passed'] for p in repeats),'invalid_requests':len(invalid),'invalid_bytes':len(invalid)*CAPACITY,'all_invalid_unchanged':all(p['passed'] for p in invalid),'imports':len(execution['imports']),'second_runtime_cases':200,'second_runtime_passed':all(p['passed'] for p in rows),'mutation_cases_per_runtime':160,'scope':'Primary-only declared premultiplied callback-target contract with integer alpha eighths and layer order. Native padding prefix and independently predicted entire16384-byte allocations/tail; V8 and WasmKit on macOS. No native getter/PNG match, Swift parsing expansion, browser, Linux or Canvas transport claim.'}


PORTABLE_RUN='20261010T185525Z-portable-primary-layer-control-596eab9a'
PORTABLE_ANCHOR='bc1c5bb6b54b5263fa4b1a1b56beb9f729c8ff5b81629059cb9fb6b243cf99f8'

def mutants(out):
    controller=Controller(root=PROJECT_ROOT);v=controller.verify(PORTABLE_RUN,PORTABLE_ANCHOR)
    if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Portable layer anchor changed')
    prior=controller.runs/PORTABLE_RUN
    identities=load(prior/'output/identities.json')
    for key,name in (('clang','clang'),('wasm_ld','wasm-ld'),('wasmkit','wasmkit')):
        if digest(TOOLCHAIN/name)!=identities[key]:raise ValueError('Portable mutation toolchain identity changed')
    source=(prior/'source/tools/re/fixtures/portable_layers.c').read_text()
    edits={'source-alpha-truncation':('(inputs[channel]*255+4)/8','(inputs[channel]*255)/8'),
           'forward-layer-order':('forward[3]={2,0,1}','forward[3]={2,1,0}')}
    atomic(out/'predictions.json',{'source_run':PORTABLE_RUN,'source_anchor':PORTABLE_ANCHOR,'mutations':edits,
        'expectations':'Both algorithm mutations preserve endpoint controls, fail at least one native target and return rejected aggregate; V8 and WasmKit witness counts equal. Frozen native arrays contain no implementation formula.'})
    (out/'layer_expectations.h').write_bytes((prior/'output/layer_expectations.h').read_bytes())
    checker_source=prior/'source/tools/re/fixtures/portable_layers_verify.c';rows=[]
    flags=['--target=wasm32','-O2','-nostdlib','-fno-builtin','-fuse-ld='+str(TOOLCHAIN/'wasm-ld'),'-Wl,--no-entry','-Wl,--initial-memory=131072','-Wl,--max-memory=131072']
    def command(args,name):
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:subprocess.run([str(a) for a in args],stdout=stdout,stderr=stderr,check=True,timeout=30)
    for name,(old,new) in edits.items():
        if source.count(old)!=1:raise ValueError('Semantic mutation edit no longer unique')
        mutant=out/(name+'.c');mutant.write_text(source.replace(old,new));ir=out/(name+'.ll');module=out/(name+'.wasm')
        command([TOOLCHAIN/'clang','--target=wasm32','-O2','-nostdlib','-fno-builtin','-emit-llvm','-S',mutant,'-o',ir],name+'-emit')
        command([TOOLCHAIN/'clang',*flags,ir,checker_source,'-I',out,'-Wl,--export=verify','-Wl,--export=verify_all','-o',module],name+'-link')
        command(['node',ROOT/'tools/re/reloop/portable_layers_fault_runner.js',module,out/(name+'.json')],name+'-v8')
        node=load(out/(name+'.json'))
        command([TOOLCHAIN/'wasmkit','run',module,'verify_all','i32:0'],name+'-wasmkit-reject')
        aggregate=parse_result((out/(name+'-wasmkit-reject.stdout')).read_text())
        command([TOOLCHAIN/'wasmkit','run',module,'verify','i32:8','i32:0'],name+'-wasmkit-witness')
        witness=parse_result((out/(name+'-wasmkit-witness.stdout')).read_text())
        rows.append({'mutation':name,'changed_cases':sum(r['mismatches']>0 for r in node['rows']),
            'endpoint_controls':all(r['mismatches']==0 for r in node['rows'][:8]),'v8_witness':node['witness'],'wasmkit_witness':witness,
            'aggregate_rejected':aggregate==0xffffffff,'witness_equal':witness==node['witness'] and 0<witness<16384,'ir_sha256':digest(ir),'module_sha256':digest(module)})
    atomic(out/'mutations.json',rows)
    return {'algorithm_mutants':len(rows),'native_cases_per_mutant':40,'all_detected':all(r['changed_cases']>0 and r['aggregate_rejected'] for r in rows),
        'all_endpoints_equal':all(r['endpoint_controls'] for r in rows),'all_witnesses_equal':all(r['witness_equal'] for r in rows),
        'scope':'Two deliberate algorithm mutants versus frozen native padded targets; V8 full per-case counts and WasmKit aggregate rejection/witness agreement. No new native acquisition or getter/Canvas conformance claim.'}
