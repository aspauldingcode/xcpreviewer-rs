"""Bounded Rust target-library/linker inventory; not a full OS dependency closure."""
import hashlib,os,stat,subprocess
from pathlib import Path
from reloop.core import canonical_hash

def file_identity(path):
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>268435456:raise ValueError('Bounded regular toolchain input required')
        h=hashlib.sha256();total=0
        while True:
            block=os.read(fd,1048576)
            if not block:break
            total+=len(block)
            if total>268435456:raise ValueError('Toolchain input grew beyond limit')
            h.update(block)
        after=os.fstat(fd)
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) or total!=before.st_size:raise ValueError('Toolchain input changed during inventory')
        return {'bytes':total,'sha256':h.hexdigest()}
    finally:os.close(fd)

def snapshot(compiler):
    compiler=Path(compiler)
    if not compiler.is_absolute() or compiler.is_symlink():raise ValueError('Absolute actual compiler required')
    def query(*args):return subprocess.run([str(compiler),*args],capture_output=True,check=True,timeout=3).stdout.decode().strip()
    libdir=Path(query('--target','wasm32-wasip1','--print','target-libdir'));sysroot=Path(query('--print','sysroot'))
    if not libdir.is_relative_to(sysroot):raise ValueError('Target libraries outside sysroot')
    inventory={}
    for path in sorted(libdir.rglob('*')):
        if path.is_symlink():raise ValueError('Symlink target input rejected')
        if path.is_file():
            inventory[str(path.relative_to(libdir))]=file_identity(path)
            if len(inventory)>128 or sum(x['bytes'] for x in inventory.values())>268435456:raise ValueError('Target inventory limit')
    if not inventory:raise ValueError('Target libraries missing')
    host=query('-vV');hostline=next(x for x in host.splitlines() if x.startswith('host: '));linkdir=sysroot/'lib/rustlib'/hostline[6:] /'bin'
    linkers={name:file_identity(linkdir/name) for name in ['rust-lld','gcc-ld/wasm-ld']}
    identity={'target':'wasm32-wasip1','compiler':str(compiler),'compiler_file':file_identity(compiler),'compiler_version':host,'target_libdir':str(libdir),'target_files':inventory,'linkers':linkers,'scope':'Actual compiler, installed target libraries and selected installed linker files; excludes complete dynamic-library/OS dependency closure'}
    return identity,canonical_hash(identity)
