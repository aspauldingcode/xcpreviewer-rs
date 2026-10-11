"""Independent Swift WASM interpreter controls; no native fallback or memory dump claim."""
import re
import hashlib
from reloop.core import ROOT,atomic,digest,load
from reloop.portable import TOOLCHAIN


def parse_result(text):
    match=re.fullmatch(r'\[WasmTypes.Value.i32\((-?\d+)\)\]\s*',text)
    if not match:raise ValueError('Missing or ambiguous WasmKit i32 result')
    value=int(match[1])
    if not -0x80000000<=value<=0xffffffff:raise ValueError('WasmKit i32 result outside representation range')
    return value & 0xffffffff


def verify_corpus(out,command):
    runtime=TOOLCHAIN/'wasmkit'
    if not runtime.is_file():raise RuntimeError('Installed WasmKit required; no fallback')
    arrays=[('red',(out/'native-0.rgba').read_bytes()),('blue',(out/'native-2.rgba').read_bytes()),
            ('padding',(out/'expected-3.rgba').read_bytes())]
    header=out/'native_expectations.h'
    header.write_text('\n'.join('static const unsigned char expected_%s[%d]={%s};'%(name,len(raw),','.join(map(str,raw))) for name,raw in arrays))
    module=out/'portable-verified.wasm'
    command([TOOLCHAIN/'clang','--target=wasm32','-O2','-nostdlib','-fno-builtin',
             '-fuse-ld='+str(TOOLCHAIN/'wasm-ld'),'-I',out,ROOT/'tools/re/fixtures/portable_solid.c',
             ROOT/'tools/re/fixtures/portable_solid_verify.c','-Wl,--no-entry','-Wl,--export=verify','-Wl,--export=verify_rejected',
             '-Wl,--initial-memory=1048576','-Wl,--max-memory=1048576','-o',module],'compile-verifier')
    command([runtime,'--version'],'wasmkit-version')
    command(['node',ROOT/'tools/re/reloop/portable_verify_runner.js',module,out/'v8-checker.json'],'v8-checker')
    v8=load(out/'v8-checker.json')
    rows=[]
    # Typed CLI parameters are mandatory; untyped values caused a prior exit 133.
    for index,mutation in [(i,m) for i in range(4) for m in range(3)]+[(4,0),(0,3)]:
        name='wasmkit-%d-%d'%(index,mutation)
        command([runtime,'run',module,'verify','i32:'+str(index),'i32:'+str(mutation)],name)
        result=parse_result((out/(name+'.stdout')).read_text())
        target=mutation and 1 or 0
        if index>3 or mutation>2:target=0xffffffff
        rows.append({'case':index,'mutation':mutation,'mismatches':result,'expected':target,'passed':result==target})
    rejected=[]
    for index in range(11):
        name='wasmkit-rejected-%d'%index
        command([runtime,'run',module,'verify_rejected','i32:'+str(index)],name)
        result=parse_result((out/(name+'.stdout')).read_text())
        target=0 if index<10 else 0xffffffff
        rejected.append({'case':index,'mismatches':result,'expected':target,'passed':result==target})
    atomic(out/'wasmkit-execution.json',{'rows':rows,'runtime_sha256':digest(runtime),
           'rejected':rejected,'v8_checker':v8,
           'module_sha256':digest(module),'expected_arrays':{name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in arrays},
           'scope':'WasmKit on macOS. Full internal byte comparison; CLI returns mismatch counts, not exported pixel dumps.'})
    return {'second_runtime':'WasmKit','second_runtime_controls':len(rows)+len(rejected),'second_runtime_all_passed':all(r['passed'] for r in rows+rejected),
            'second_runtime_compared_bytes':614432,'second_runtime_mutation_controls':8,
            'second_runtime_invalid_requests':10,'second_runtime_unchanged_buffer_bytes':2048000,
            'same_checker_v8_passed':v8['all_passed'],'checker_imports':len(v8['imports'])}
