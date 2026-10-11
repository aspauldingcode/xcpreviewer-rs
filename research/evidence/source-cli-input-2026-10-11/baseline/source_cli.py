#!/usr/bin/env python3
"""Build only the declared literal primary-layer source subset; no native fallback."""
import argparse
import json
import pathlib
import sys
from reloop.sourcecache import build

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=pathlib.Path)
    for name in ('cache','output','clang','wasm-ld'):parser.add_argument('--'+name,required=True,type=pathlib.Path)
    args=parser.parse_args()
    try:
        if args.source.stat().st_size>4096:raise ValueError('Bounded source file required')
        result=build(args.source.read_text(),args.cache,args.output,args.clang,args.wasm_ld)
    except Exception as error:
        print(json.dumps({'ok':False,'error_type':type(error).__name__,'error':str(error)}),file=sys.stderr);return 1
    print(json.dumps({'ok':True,**result}));return 0

if __name__=='__main__':sys.exit(main())
