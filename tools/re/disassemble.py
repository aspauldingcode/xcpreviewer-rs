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
parser.add_argument('--range',dest='ranges',action='append',default=[],help='Explicit aligned start:stop hex range, at most 4096 bytes')
parser.add_argument('--query', default='^$', help='Regular expression matched against demangled names')
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
if args.ranges:
    from reloop.core import validate_experiment
    from reloop.swiftmeta import MachO
    validate_experiment({'id':'range-validation','adapter':'disassembly','hypothesis':'Validate bounded instruction ranges','depends_on':[],'resources':[],'timeout_seconds':30,'artifact_limit_mb':8,'params':{'ranges':args.ranges},'priority':1,'checks':[{'path':'valid','equals':True}]})
    image=MachO(args.binary)
    for value in args.ranges:
        start,stop=(int(v,16) for v in value.split(':'))
        if not any(s['disk'] and s['address']<=start and stop<=s['address']+s['size'] for s in image.sections):raise ValueError('Instruction range must fit one file-backed section')
        key=format(start,'016x')
        if key in seen:raise ValueError('Range overlaps a selected entry')
        output=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(start),'--stop-address='+hex(stop),args.binary],capture_output=True,text=True,check=True,timeout=30).stdout
        output=normalize_words(output)
        if not has_entry(output,start):raise ValueError('Explicit range lacks instruction evidence')
        (args.out/(key+'.txt')).write_text('Explicit bounded range '+value+'\n'+output)
        row={'entry':hex(start),'stop':hex(stop),'mode':'explicit-address','entry_instruction':True,'aliases':[]}
        selections.append(row);seen[key]=row;count+=1
(args.out/'selection.json').write_text(json.dumps(selections,indent=2)+'\n')
print(f'Disassembled {count} functions into {args.out}')
raise SystemExit(0 if count else 1)
