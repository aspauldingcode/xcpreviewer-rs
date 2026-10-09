#!/usr/bin/env python3
"""Disassemble named symbols or addresses from the local preview messaging image."""
import argparse
import pathlib
import re
import subprocess
import json
from reloop.disassembly import has_entry,normalize_words

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', default='/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost')
parser.add_argument('--out', type=pathlib.Path, default=pathlib.Path('research/raw/disassembly'))
parser.add_argument('--query', required=True, help='Regular expression matched against demangled names')
args = parser.parse_args()
query = re.compile(args.query)
raw = subprocess.run(['nm', args.binary], capture_output=True, text=True, check=True,timeout=30).stdout
result = subprocess.run(['xcrun', 'swift-demangle'], input=raw, capture_output=True, text=True, check=True,timeout=30).stdout
args.out.mkdir(parents=True, exist_ok=True)
count = 0
addresses=sorted({int(parts[0],16) for line in raw.splitlines() if len(parts:=line.split())==3 and parts[1].lower()=='t'})
selections=[]
seen={}
for line, demangled in zip(raw.splitlines(), result.splitlines()):
    parts = line.split()
    if len(parts) != 3 or parts[1].lower() != 't' or not query.search(demangled):
        continue
    address, _, symbol = parts
    if address in seen:
        seen[address]['aliases'].append(demangled)
        continue
    output = subprocess.run(['xcrun', 'llvm-objdump', '--macho', '--arch=arm64', '--disassemble', '--dis-symname', symbol, args.binary], capture_output=True, text=True, check=True,timeout=30).stdout
    mode='macho-symbol';entry=int(address,16);stop=None
    if not has_entry(output,entry):
        (args.out / f'{address}.primary.log').write_text(output)
        following=next((v for v in addresses if v>entry),None)
        if following is None or following-entry>65536:raise ValueError('No bounded next text symbol for empty-body fallback')
        stop=following;mode='bounded-address'
        output=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble',
                               '--start-address='+hex(entry),'--stop-address='+hex(stop),args.binary],
                              capture_output=True,text=True,check=True,timeout=30).stdout
        output=normalize_words(output)
    if not has_entry(output,entry):raise ValueError('Selected native entry lacks instruction evidence')
    (args.out / f'{address}.txt').write_text(demangled + '\n' + output)
    row={'entry':hex(entry),'stop':hex(stop) if stop else None,'mode':mode,'entry_instruction':True,'aliases':[demangled]}
    selections.append(row);seen[address]=row
    count += 1
(args.out/'selection.json').write_text(json.dumps(selections,indent=2)+'\n')
print(f'Disassembled {count} functions into {args.out}')
raise SystemExit(0 if count else 1)
