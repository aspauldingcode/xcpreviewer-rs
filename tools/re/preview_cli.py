#!/usr/bin/env python3
"""Render the supported primary-layer source subset to a verified frame and PNG."""
import argparse
import json
import pathlib
from reloop.sourceframe import render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=pathlib.Path)
    for key in ('cache', 'output', 'clang', 'wasm-ld', 'node'):
        parser.add_argument('--' + key, required=True, type=pathlib.Path)
    parser.add_argument('--stride', type=int)
    parser.add_argument('--runtime-seconds', type=float, default=5)
    args = parser.parse_args()
    try:
        with args.source.open('rb') as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            raise ValueError('Bounded source file required')
        receipt = render(raw.decode('ascii'), args.cache, args.output, args.clang,
                         args.wasm_ld, args.node, stride=args.stride, timeout=args.runtime_seconds)
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__, 'error': str(error)}))
        return 1
    print(json.dumps({'ok': True, **receipt}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
