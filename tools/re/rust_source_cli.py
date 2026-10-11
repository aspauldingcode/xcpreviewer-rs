#!/usr/bin/env python3
"""Finite primary-expression frontend into owned Rust WASM; not a Swift compiler."""
import argparse,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
from reloop.core import ROOT,digest
from reloop.primarysource import parse
from reloop.rustidentity import snapshot

def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--output',required=True);p.add_argument('--rustc',required=True);p.add_argument('--rustc-sha256',required=True);p.add_argument('--toolchain-pin',required=True);a=p.parse_args()
    fd=os.open(a.source,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>4096:raise ValueError('Bounded regular source required')
        raw=os.read(fd,4097);after=os.fstat(fd)
        if len(raw)>4096 or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('Source changed during read')
    finally:os.close(fd)
    config=parse(raw.decode('ascii'))
    compiler=Path(a.rustc)
    if not compiler.is_absolute() or compiler.is_symlink() or digest(compiler)!=a.rustc_sha256:raise ValueError('Pinned Rust compiler identity changed')
    toolchain,toolchain_sha=snapshot(compiler)
    if toolchain_sha!=a.toolchain_pin:raise ValueError('Pinned Rust target/linker identity changed')
    source=ROOT/'tools/re/rust/canvas-core/src';contract=source/'contract.rs';template=source/'wasm-template.rs';pins={name:digest(source/name) for name in ['contract.rs','wasm-template.rs']}
    text=template.read_text().replace('CONTRACT_PATH',str(contract))
    values={'WIDTH':config['width'],'HEIGHT':config['height'],'RED':config['alphas'][0],'GREEN':config['alphas'][1],'BLUE':config['alphas'][2],'REVERSE':'true' if config['reverse'] else 'false'}
    for k,v in values.items():text=text.replace(k,str(v))
    out=Path(a.output);out.mkdir(exist_ok=False);generated=out/'module.rs';generated.write_text(text);module=out/'view.wasm'
    args=[str(compiler),'--edition=2021','--target','wasm32-wasip1','--crate-type','cdylib','-C','panic=abort','-C','opt-level=2','-C','link-arg=--initial-memory=131072','-C','link-arg=--max-memory=131072','-C','link-arg=-zstack-size=8192',str(generated),'-o',str(module)]
    r=subprocess.run(args,capture_output=True,timeout=20);(out/'compile.stderr').write_bytes(r.stderr);r.check_returncode()
    if digest(compiler)!=a.rustc_sha256 or pins!={name:digest(source/name) for name in pins}:raise ValueError('Compiler/source identity changed during build')
    if snapshot(compiler)[1]!=toolchain_sha:raise ValueError('Target/linker identity changed during build')
    receipt={'source_sha256':hashlib.sha256(raw).hexdigest(),'module_sha256':digest(module),'config':config,'rustc_sha256':a.rustc_sha256,'toolchain_sha256':toolchain_sha,'sources':pins,'generated_sha256':digest(generated),'cache_hit':False,'target':'wasm32-wasip1','scope':'Finite primary literal expression lowering; not general Swift compilation'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
    try:main()
    except (ValueError,OSError,UnicodeError,subprocess.SubprocessError) as e:print('rejected '+str(e),file=sys.stderr);sys.exit(2)
