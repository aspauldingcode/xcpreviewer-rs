#!/usr/bin/env python3
"""Disassemble named symbols or addresses from the local preview messaging image."""
import argparse
import pathlib
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', default='/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost')
parser.add_argument('--out', type=pathlib.Path, default=pathlib.Path('research/raw/disassembly'))
parser.add_argument('--query', required=True, help='Regular expression matched against demangled names')
args = parser.parse_args()
query = re.compile(args.query)
raw = subprocess.run(['nm', args.binary], capture_output=True, text=True, check=True).stdout
result = subprocess.run(['xcrun', 'swift-demangle'], input=raw, capture_output=True, text=True, check=True).stdout
args.out.mkdir(parents=True, exist_ok=True)
count = 0
for line, demangled in zip(raw.splitlines(), result.splitlines()):
    parts = line.split()
    if len(parts) != 3 or parts[1].lower() != 't' or not query.search(demangled):
        continue
    address, _, symbol = parts
    output = subprocess.run(['xcrun', 'llvm-objdump', '--macho', '--arch=arm64', '--disassemble', '--dis-symname', symbol, args.binary], capture_output=True, text=True, check=True).stdout
    (args.out / f'{address}.txt').write_text(demangled + '\n' + output)
    count += 1
print(f'Disassembled {count} functions into {args.out}')
raise SystemExit(0 if count else 1)
