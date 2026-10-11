#!/usr/bin/env python3
"""Build only the declared literal primary-layer source subset; no native fallback."""
import argparse
import json
import pathlib
import os
import stat
import sys
from reloop.sourcecache import build

def read_source(path):
    """Read one bounded ASCII POSIX regular file without following links."""
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>4096:
            raise ValueError('Bounded regular source file required')
        raw=os.read(fd,4097)
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        if len(raw)>4096 or identity(before)!=identity(after):
            raise ValueError('Source changed during read')
        return raw.decode('ascii')
    finally:
        os.close(fd)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=pathlib.Path)
    for name in ('cache','output','clang','wasm-ld'):parser.add_argument('--'+name,required=True,type=pathlib.Path)
    args=parser.parse_args()
    try:
        result=build(read_source(args.source),args.cache,args.output,args.clang,args.wasm_ld)
    except Exception as error:
        print(json.dumps({'ok':False,'error_type':type(error).__name__,'error':str(error)}),file=sys.stderr);return 1
    print(json.dumps({'ok':True,**result}));return 0

if __name__=='__main__':sys.exit(main())
