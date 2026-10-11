"""Native-backed eighth-step alpha reconstruction, independent full-buffer controls."""
import math
import pathlib
import subprocess
from PIL import Image
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.portable import TOOLCHAIN
from reloop.verification import bytes_equal
from reloop.wasmkit import parse_result

ORACLE_RUN='20261010T165943Z-native-alpha-quantized-compositing-33ebc0eb'
ORACLE_ANCHOR='4377ef5efe83e95dd1d092eb80c2551ae9fac9312a61a5748a1a4902c8114a48'
CASES=((0,0),(2,0),(4,0),(8,0),(2,1),(4,1),(1,1),(6,1))
CAPACITY=16384


def expected(w,h,stride,n,bg):
    args=(w,h,stride,n,bg)
    if any(type(a) is not int for a in args) or not (1<=w<=64 and 1<=h<=64 and w*4<=stride<=256 and 0<=n<=8 and bg in (0,1)):
        raise ValueError('Unsupported alpha rectangle')
    alpha=math.floor((n/8)*255+.5)
    pixel=bytes((alpha,0,255-alpha,255) if bg else (255 if alpha else 0,0,0,alpha))
    raw=(pixel*w+b'\xcd'*(stride-w*4))*h
    return raw+b'\xa5'*(CAPACITY-len(raw))


def corpus(out):
    anchor=Controller(root=PROJECT_ROOT).verify(ORACLE_RUN,ORACLE_ANCHOR)
    if not anchor['valid']:raise RuntimeError('Native alpha anchor mismatch')
    atomic(out/'native-anchor.json',anchor)
    native=PROJECT_ROOT/'research/runs'/ORACLE_RUN/'output'
    native_pixels=[]
    for variant in range(8):
        with Image.open(native/('alpha-%d-0.png'%variant)) as image:
            if image.size!=(17,9):raise RuntimeError('Native alpha geometry mismatch')
            raw=image.convert('RGBA').tobytes()
        native_pixels.append(raw);(out/('native-%d.rgba'%variant)).write_bytes(raw)
    def command(args,name):
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
            subprocess.run([str(a) for a in args],stdout=stdout,stderr=stderr,check=True,timeout=30)
    source=ROOT/'tools/re/fixtures/portable_alpha.c';ir=out/'alpha.ll';module=out/'alpha.wasm'
    clang=TOOLCHAIN/'clang';linker=TOOLCHAIN/'wasm-ld'
    command([clang,'--version'],'clang-version')
    command([clang,'--target=wasm32','-O2','-nostdlib','-fno-builtin','-emit-llvm','-S',source,'-o',ir],'emit-ir')
    flags=['--target=wasm32','-O2','-nostdlib','-fno-builtin','-fuse-ld='+str(linker),'-Wl,--no-entry','-Wl,--initial-memory=131072','-Wl,--max-memory=131072']
    command([clang,*flags,ir,'-Wl,--export=render','-Wl,--export=pixels','-Wl,--export=capacity','-o',module],'link')
    runner=ROOT/'tools/re/reloop/portable_alpha_runner.js'
    command(['node',runner,module,out],'v8')
    execution=load(out/'execution.json');comparisons=[];native_checks=[];repeat_checks=[]
    for row in execution['rows']:
        i=row['index'];prediction=out/('expected-%d.rgba'%i)
        prediction.write_bytes(expected(row['w'],row['h'],row['stride'],row['n'],row['bg']))
        comparisons.append(bytes_equal(prediction,out/('frame-%d.rgba'%i)))
        if row['repeat']==1:repeat_checks.append(bytes_equal(out/('frame-%d.rgba'%(i-1)),out/('frame-%d.rgba'%i)))
        if (row['n'],row['bg']) in CASES and (row['w'],row['h'],row['stride'])==(17,9,68):
            variant=CASES.index((row['n'],row['bg']));active=out/('active-%d.rgba'%i)
            active.write_bytes((out/('frame-%d.rgba'%i)).read_bytes()[:612])
            native_checks.append(bytes_equal(out/('native-%d.rgba'%variant),active))
    invalid_prediction=out/'invalid-expected.rgba';invalid_prediction.write_bytes(expected(17,9,80,4,1))
    invalid_baseline=bytes_equal(invalid_prediction,out/'invalid-before.rgba')
    if not invalid_baseline['passed']:raise RuntimeError('Invalid-request baseline mismatches independent allocation')
    invalid=[bytes_equal(out/'invalid-before.rgba',out/('invalid-%d.rgba'%i)) for i in range(len(execution['invalid']))]
    atomic(out/'comparisons.json',{'allocations':comparisons,'native':native_checks,'repeats':repeat_checks,'invalid':invalid})
    (out/'alpha_expectations.h').write_text('static const unsigned char native_pixels[8][612]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in native_pixels)+'};\n')
    checker=out/'alpha-checker.wasm'
    # Link the exact saved renderer IR, no LTO; checker expectations come from native captures.
    command([clang,*flags,ir,ROOT/'tools/re/fixtures/portable_alpha_verify.c','-I',out,'-Wl,--export=verify','-o',checker],'checker-link')
    command(['node',runner,checker,out,'checker'],'checker-v8')
    rows=[]
    for variant in range(8):
        for mutation in range(4):
            name='wasmkit-%d-%d'%(variant,mutation)
            command([TOOLCHAIN/'wasmkit','run',checker,'verify','i32:'+str(variant),'i32:'+str(mutation)],name)
            count=parse_result((out/(name+'.stdout')).read_text())
            rows.append({'variant':variant,'mutation':mutation,'mismatches':count,'passed':count==(1 if mutation else 0)})
    atomic(out/'wasmkit.json',rows)
    atomic(out/'identities.json',{'clang':digest(clang),'wasm_ld':digest(linker),'wasmkit':digest(TOOLCHAIN/'wasmkit'),'renderer_ir':digest(ir),'renderer_module':digest(module),'checker_module':digest(checker),'source':digest(source),'node':execution['node'],'v8':execution['v8']})
    return {'frames':len(comparisons),'all_allocations_equal':all(c['passed'] for c in comparisons),'allocation_bytes':sum(c['reference_bytes'] for c in comparisons),
            'native_frames':len(native_checks),'native_bytes':sum(c['reference_bytes'] for c in native_checks),'all_native_equal':all(c['passed'] for c in native_checks),
            'repeat_pairs':len(repeat_checks),'all_repeats_equal':all(c['passed'] for c in repeat_checks),'invalid_requests':len(invalid),'invalid_bytes':sum(c['reference_bytes'] for c in invalid),'all_invalid_unchanged':all(c['passed'] for c in invalid),
            'imports':len(execution['imports']),'second_runtime_controls':len(rows),'second_runtime_passed':all(r['passed'] for r in rows),'mutation_controls':24,
            'scope':'Explicit eighth-step red alpha/optional blue subset. Native17x9 holdouts plus model-only remaining cases; entire16384-byte allocation, padding and tail. Node V8 and native-backed checker in WasmKit on macOS. No Swift parser expansion, arbitrary colors, Canvas wire or other platform/browser/performance claim.'}
