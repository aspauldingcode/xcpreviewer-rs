"""Bounded primary-layer build cache and atomic published-bundle pointer.

Integrity detects inconsistent local cache edits; it is not cache authenticity.
"""
import contextlib
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
from reloop.core import atomic,digest,load
from reloop.primarysource import parse,lower
from reloop.viewsource import stable_ir

FILES=('view.c','view.ll','view.wasm')
PAYLOAD_LIMITS={'view.c':65536,'view.ll':4194304,'view.wasm':4194304}
FLAGS=['--target=wasm32','-O2','-nostdlib','-fno-builtin']
LINK_FLAGS=['-Wl,--no-entry','-Wl,--strip-all','-Wl,--initial-memory=131072','-Wl,--max-memory=131072','-Wl,--export=render','-Wl,--export=pixels','-Wl,--export=capacity']


def read_metadata(path,limit):
    """Bounded regular metadata read; local POSIX cache integrity only."""
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>limit:
            raise ValueError('Bounded regular cache metadata required')
        raw=os.read(fd,limit+1)
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        if len(raw)>limit or len(raw)!=before.st_size or identity(before)!=identity(after):
            raise ValueError('Cache metadata changed during read')
        return raw
    finally:
        os.close(fd)


def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def directory(path):
    path=pathlib.Path(path)
    if path.is_symlink():raise ValueError('Symlink directory rejected')
    path.mkdir(parents=True,exist_ok=True)
    if not path.is_dir():raise ValueError('Directory required')
    return path


@contextlib.contextmanager
def lock(root,name):
    path=root/name
    if path.is_symlink():raise ValueError('Symlink lock rejected')
    with path.open('a+') as file:
        try:fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Owned build/publish lock busy')
        try:yield
        finally:fcntl.flock(file,fcntl.LOCK_UN)


def entry(folder,key,identity,anchor):
    if type(anchor) is not str or not re.fullmatch('[0-9a-f]{64}',anchor):raise ValueError('Cache anchor shape')
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Cache entry directory')
    if any(p.is_symlink() for p in folder.iterdir()):raise ValueError('Cache symlink rejected')
    if {p.name for p in folder.iterdir()}!=set(FILES)|{'manifest.json'}:raise ValueError('Cache inventory changed')
    raw=read_metadata(folder/'manifest.json',65536)
    if hashlib.sha256(raw).hexdigest()!=anchor:raise ValueError('Cache manifest anchor changed')
    m=json.loads(raw)
    if type(m) is not dict or set(m)!={'version','cache_key','identity','files'} or m['version']!=1 or type(m['version']) is not int or m['cache_key']!=key or fingerprint(m['identity'])!=fingerprint(identity) or type(m['files']) is not dict or set(m['files'])!=set(FILES):raise ValueError('Cache identity changed')
    payloads={}
    for name in FILES:
        row=m['files'][name]
        if type(row) is not dict or set(row)!={'sha256','bytes'} or type(row['bytes']) is not int or not 0<=row['bytes']<=PAYLOAD_LIMITS[name]:
            raise ValueError('Cache payload size limit')
        raw=read_metadata(folder/name,PAYLOAD_LIMITS[name])
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Cache payload changed')
        payloads[name]=raw
    if payloads['view.wasm'][:8]!=b'\0asm\x01\0\0\0':raise ValueError('WASM header changed')
    if payloads['view.c']!=lower(identity['config']).encode():raise ValueError('Cache lowered source changed')
    return m


def build(source,cache,output,clang,wasm_ld,*,fault_before_commit=False):
    if type(source) is not str:raise ValueError('Source text required')
    config=parse(source);clang=pathlib.Path(clang).absolute();wasm_ld=pathlib.Path(wasm_ld).absolute()
    if not clang.is_file() or not wasm_ld.is_file():raise ValueError('Compiler/linker executable required')
    identity={'version':1,'config':config,'target':'wasm32','flags':FLAGS,'link_flags':LINK_FLAGS,'builder_sha256':digest(__file__),'ir_normalizer_sha256':digest(pathlib.Path(__file__).with_name('viewsource.py')),'clang_invocation':str(clang),'wasm_ld_invocation':str(wasm_ld),'clang_sha256':digest(clang),'wasm_ld_sha256':digest(wasm_ld),'lowerer_sha256':digest(pathlib.Path(__file__).with_name('primarysource.py')),'kernel_sha256':hashlib.sha256(lower(config).encode()).hexdigest()}
    key=fingerprint(identity);cache=directory(cache);output=directory(output)
    with lock(cache,'.build.lock'),lock(output,'.publish.lock'):
        entries=directory(cache/'entries');keys=directory(cache/'keys');versions=directory(output/'versions');index=keys/(key+'.json')
        if index.is_symlink():raise ValueError('Cache index symlink')
        hit=index.exists()
        if hit:
            pin=json.loads(read_metadata(index,4096))
            if type(pin) is not dict or set(pin)!={'version','entry_sha256'} or type(pin['version']) is not int or pin['version']!=1:raise ValueError('Cache index schema')
            anchor=pin['entry_sha256']
            if type(anchor) is not str or not re.fullmatch('[0-9a-f]{64}',anchor):raise ValueError('Cache index anchor')
            folder=entries/anchor;m=entry(folder,key,identity,anchor)
        else:
            staging=pathlib.Path(tempfile.mkdtemp(prefix='.owned-build-',dir=cache))
            try:
                c=staging/'view.c';ir=staging/'view.ll';module=staging/'view.wasm';c.write_text(lower(config))
                def command(args):
                    r=subprocess.run([str(a) for a in args],capture_output=True,timeout=30)
                    if r.returncode:raise RuntimeError('Compiler failed: '+r.stderr.decode(errors='replace')[-4096:])
                command([clang,*FLAGS,'-emit-llvm','-S',c,'-o',ir]);ir.write_text(stable_ir(ir.read_text()))
                command([clang,*FLAGS,'-fuse-ld='+str(wasm_ld),ir,*LINK_FLAGS,'-o',module])
                m={'version':1,'cache_key':key,'identity':identity,'files':{n:{'sha256':digest(staging/n),'bytes':(staging/n).stat().st_size} for n in FILES}}
                atomic(staging/'manifest.json',m);anchor=digest(staging/'manifest.json');folder=entries/anchor
                entry(staging,key,identity,anchor)
                if folder.exists():entry(folder,key,identity,anchor)
                else:os.replace(staging,folder)
                atomic(index,{'version':1,'entry_sha256':anchor})
            finally:
                if staging.exists():shutil.rmtree(staging)
        published=versions/anchor
        if published.exists():entry(published,key,identity,anchor)
        else:
            staging=pathlib.Path(tempfile.mkdtemp(prefix='.owned-publish-',dir=output))
            try:
                for name in (*FILES,'manifest.json'):shutil.copyfile(folder/name,staging/name)
                entry(staging,key,identity,anchor);os.replace(staging,published)
            finally:
                if staging.exists():shutil.rmtree(staging)
        receipt={'version':1,'cache_key':key,'entry_sha256':anchor,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'module_sha256':m['files']['view.wasm']['sha256'],'module':'versions/'+anchor+'/view.wasm','config':config}
        if fault_before_commit:raise RuntimeError('Owned pre-publication fault')
        if (output/'current.json').is_symlink():raise ValueError('Publish pointer symlink')
        atomic(output/'current.json',receipt)
    return {**receipt,'cache_hit':hit,'scope':'Strict explicit primary-layer source subset to cached WASM, atomic single published-bundle pointer. No runtime/state preservation, stale generation, watcher, native Canvas or general SwiftUI claim.'}
