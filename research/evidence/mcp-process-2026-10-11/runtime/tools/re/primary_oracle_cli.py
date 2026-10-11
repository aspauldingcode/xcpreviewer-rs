#!/usr/bin/env python3
"""Bounded finite primary-expression byte oracle; not a Swift compiler."""
import sys
from reloop.primarysource import parse,expected

def main():
    raw=sys.stdin.buffer.read(4097)
    if not raw or len(raw)>4096:raise ValueError('Source byte bound')
    allocation=expected(parse(raw.decode('ascii')),64)
    if len(allocation)!=16384:raise ValueError('Allocation byte bound')
    sys.stdout.buffer.write(allocation)

if __name__=='__main__':
    try:main()
    except Exception:
        print('Unsupported finite primary expression',file=sys.stderr);sys.exit(2)
