"""Narrow static interpretation of the observed ARM64 enum string getter.

No native Swift call or enum ABI declaration is manufactured. Unknown instructions,
unmapped reads and unrecognized String forms stop extraction.
"""
import pathlib
import re
import subprocess
from reloop.core import atomic, digest
from reloop.swiftmeta import MachO, inspect

SYMBOL='_$s21PreviewsMessagingHost16AgentMessageTypeO8rawValueSSvg'
IMAGE='/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost'
MASK=(1<<64)-1


def instructions(text):
    parsed={}
    for line in text.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+){4})([a-z0-9.]+)\s*(.*)$',line)
        if match:
            address=int(match[1],16)
            parsed[address]=(match[3],match[4].split(';')[0].strip(),int.from_bytes(bytes.fromhex(match[2]),'little'))
    if not parsed or len(parsed)>512:raise ValueError('Expected bounded ARM64 getter disassembly')
    return parsed


def pc_relative(word,pc,page):
    expected=0x90000000 if page else 0x10000000
    if word&0x9f000000!=expected:raise ValueError('Unexpected PC-relative instruction encoding')
    imm=((word>>5)&0x7ffff)<<2 | ((word>>29)&3)
    if imm&(1<<20):imm-=1<<21
    return (pc&~4095)+(imm<<12) if page else pc+imm


def returned_string(image,x0,x1):
    # Darwin 64-bit immortal literals only. See Swift StringObject.swift.
    if x1>>60==0xe:
        size=(x1>>56)&15
        raw=x0.to_bytes(8,'little')+x1.to_bytes(8,'little')
        return raw[:size].decode('utf-8')
    if x1>>60==8 and x0>>60==0xd:
        size=x0&0x0000ffffffffffff
        if not 1<=size<=512:raise ValueError('Literal length outside extraction bound')
        start=(x1&0x0fffffffffffffff)+32
        offset=image.file_offset(start)
        raw=image.data[offset:offset+size]
        if len(raw)!=size or image.data[offset+size:offset+size+1]!=b'\0':raise ValueError('Literal outside image or missing terminator')
        return raw.decode('utf-8')
    raise ValueError('Unsupported Swift String representation')


def interpret(image,code,selector,maximum=128):
    if type(selector) is not int or not 0<=selector<32:raise ValueError('Invalid selector')
    pc=min(code)
    if code[pc][:2]!=('ldrb','w8, [x20]'):raise ValueError('Observed enum selector load has changed')
    registers={'x8':selector};visited=[pc];pc+=4
    def read(name):
        key='x'+name[1:]
        if key not in registers:raise ValueError('Read of unknown register '+name)
        return registers[key]&((1<<32)-1 if name.startswith('w') else MASK)
    def write(name,value):registers['x'+name[1:]]=value&((1<<32)-1 if name.startswith('w') else MASK)
    def immediate(text):return int(text.lstrip('#'),0)
    for _ in range(maximum):
        if pc not in code:raise ValueError('Control flow outside selected function')
        opcode,operands,word=code[pc];visited.append(pc);args=[a.strip() for a in operands.split(',')];next_pc=pc+4
        if opcode=='ret':return {'raw_value':returned_string(image,read('x0'),read('x1')),'x0':hex(read('x0')),'x1':hex(read('x1')),'visited':[hex(p) for p in visited]}
        if opcode=='mov':write(args[0],immediate(args[1]) if args[1].startswith('#') else read(args[1]))
        elif opcode=='movk':
            shift=int(args[2].split('#')[1]) if len(args)==3 else 0
            if shift not in {0,16,32,48}:raise ValueError('Invalid movk shift')
            write(args[0],(read(args[0])&~(65535<<shift)) | (immediate(args[1])<<shift))
        elif opcode in {'adr','adrp'}:write(args[0],pc_relative(word,pc,opcode=='adrp'))
        elif opcode in {'add','sub','orr'}:
            rhs=immediate(args[2]) if args[2].startswith('#') else read(args[2])
            if len(args)==4:
                if not re.fullmatch(r'lsl #\d+',args[3]):raise ValueError('Unsupported operand shift')
                shift=int(args[3].split('#')[1])
                if not 0<=shift<=63:raise ValueError('Invalid operand shift')
                rhs<<=shift
            left=read(args[1]);write(args[0],left+rhs if opcode=='add' else left-rhs if opcode=='sub' else left|rhs)
        elif opcode=='ldrb':
            match=re.fullmatch(r'(w\d+), \[(x\d+), (x\d+)\]',operands)
            if not match:raise ValueError('Unsupported memory operand')
            offset=image.file_offset(read(match[2])+read(match[3]));write(match[1],image.data[offset])
        elif opcode=='br':next_pc=read(args[0])
        elif opcode=='b':next_pc=immediate(args[0])
        else:raise ValueError('Unsupported instruction '+opcode)
        pc=next_pc
    raise ValueError('Instruction budget exceeded')


def recover(out):
    out=pathlib.Path(out);image=MachO(IMAGE)
    if image.u32(4)!=0x100000c:raise ValueError('Expected ARM64 Mach-O')
    command=['xcrun','llvm-objdump','--macho','--arch=arm64','--disassemble','--dis-symname',SYMBOL,IMAGE]
    text=subprocess.run(command,capture_output=True,text=True,check=True,timeout=30).stdout
    (out/'getter-disassembly.txt').write_text(text);atomic(out/'command.json',command)
    code=instructions(text);metadata=inspect(IMAGE)
    matches=[t for t in metadata['types'] if t.get('name')=='AgentMessageType']
    if len(matches)!=1:raise ValueError('Expected unique AgentMessageType descriptor')
    names=[f['name'] for f in matches[0].get('fields',[])]
    if not 1<=len(names)<=32:raise ValueError('Unexpected enum case count')
    records=[{'selector_index':i,'metadata_case':name,**interpret(image,code,i)} for i,name in enumerate(names)]
    atomic(out/'agent-discriminants.json',{'image_sha256':digest(IMAGE),'image_uuid':image.uuid,
        'getter_address':hex(min(code)),'records':records,
        'scope':'Static ARM64 selector-to-String interpretation, corroborated by field descriptors. Selector indices are not numeric wire IDs; no native enum ABI call or live transport capture.'})
    return {'case_count':len(records),'unique_raw_values':len({r['raw_value'] for r in records}),
            'strings_match_case_names':all(r['raw_value']==r['metadata_case'] for r in records),
            'raw_values':[r['raw_value'] for r in records],'image_sha256':digest(IMAGE),'image_uuid':image.uuid,
            'scope':'Static getter results only; not observed live message discriminants.'}
