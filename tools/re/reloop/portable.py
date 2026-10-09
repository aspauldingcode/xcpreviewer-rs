"""LLVM-to-WASM opaque literal rectangle feasibility, separate from SwiftUI source support."""
import pathlib
import shutil
import subprocess
from PIL import Image
from reloop.core import ROOT,PROJECT_ROOT,Controller,atomic,digest,load
from reloop.verification import bytes_equal

ORACLE_RUN='20261009T155055Z-native-solid-renderer-oracle-b779b982'
ORACLE_ANCHOR='2fbbdb58072cd32f287fdd841eb072cd8f925513e4fd2c4323bf38fe11b8cf3c'
TOOLCHAIN=pathlib.Path.home()/'Library/Developer/Toolchains/swift-6.3-RELEASE.xctoolchain/usr/bin'


def expected(width,height,stride,variant):
    if not (1<=width<=320 and 1<=height<=160 and width*4<=stride<=1280 and variant in (2,3)):raise ValueError('Unsupported literal rectangle')
    pixel=bytes((255,0,0,255) if variant==2 else (0,0,255,255))
    return (pixel*width+b'\xcd'*(stride-width*4))*height


def corpus(out):
    out=pathlib.Path(out)
    verified=Controller(root=PROJECT_ROOT).verify(ORACLE_RUN,ORACLE_ANCHOR)
    if not verified['valid']:raise RuntimeError('Native oracle seal/anchor mismatch')
    atomic(out/'native-anchor.json',verified)
    source=ROOT/'tools/re/fixtures/portable_solid.c';module=out/'portable-solid.wasm';clang=TOOLCHAIN/'clang'
    def command(args,name):
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
            subprocess.run([str(a) for a in args],stdout=stdout,stderr=stderr,check=True,timeout=30)
    command([clang,'--version'],'llvm-version')
    command([clang,'--target=wasm32','-O2','-nostdlib','-fno-builtin','-emit-llvm','-S',source,'-o',out/'portable-solid.ll'],'ir')
    command([clang,'--target=wasm32','-O2','-nostdlib','-fno-builtin','-fuse-ld='+str(TOOLCHAIN/'wasm-ld'),source,
             '-Wl,--no-entry','-Wl,--export=render','-Wl,--export=pixels','-Wl,--export=capacity',
             '-Wl,--initial-memory=327680','-Wl,--max-memory=327680','-o',module],'compile')
    command([TOOLCHAIN/'llvm-objdump','-h',module],'module-sections')
    command(['node',ROOT/'tools/re/reloop/portable_solid_runner.js',module,out],'execute')
    execution=load(out/'module-execution.json');comparisons=[]
    native=PROJECT_ROOT/'research/runs'/ORACLE_RUN/'output'
    for i,row in enumerate(execution['rows']):
        reference=out/('expected-%d.rgba'%i);reference.write_bytes(expected(row['width'],row['height'],row['stride'],row['variant']))
        comparison=bytes_equal(reference,out/('portable-%d.rgba'%i));comparisons.append(comparison)
        if i<3:
            png=native/('solid-%d.png'%i);dest=out/('native-%d.png'%i);shutil.copyfile(png,dest)
            with Image.open(dest) as image:
                if image.size!=(320,160):raise RuntimeError('Native geometry mismatch')
                (out/('native-%d.rgba'%i)).write_bytes(image.convert('RGBA').tobytes())
    native_comparisons=[bytes_equal(out/('native-%d.rgba'%i),out/('portable-%d.rgba'%i)) for i in range(3)]
    atomic(out/'literal-comparisons.json',comparisons);atomic(out/'native-comparisons.json',native_comparisons)
    atomic(out/'tool-identities.json',{'clang_sha256':digest(clang),'wasm_ld_sha256':digest(TOOLCHAIN/'wasm-ld'),
           'module_sha256':digest(module),'source_sha256':digest(source),'node':execution['node'],'v8':execution['v8']})
    return {'native_frames':len(native_comparisons),'all_native_rgba_equal':all(c['passed'] for c in native_comparisons),
            'native_compared_bytes':sum(c['reference_bytes'] for c in native_comparisons),
            'all_literal_and_padding_equal':all(c['passed'] for c in comparisons),'wasm_imports':len(execution['imports']),
            'negative_cases':execution['negative_cases'],'negative_buffer_unchanged':execution['negative_buffer_unchanged'],
            'repeat_bytes_equal':bytes_equal(out/'portable-0.rgba',out/'portable-1.rgba')['passed'],
            'scope':'Hand-authored C opaque red/blue rectangle subset, LLVM wasm32, Node V8 on macOS. No Swift parsing, SwiftUI, Canvas wire, browser/other OS execution or hot reload/performance claim.'}
