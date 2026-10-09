"""Read-only Mach-O indirect symbol binding and ARM64 stub projection."""
import struct
from reloop.discriminants import instructions,pc_relative


def tables(image):
    sym=None;indirect=None;libraries=[];offset=32
    count=image.u32(16)
    for _ in range(count):
        cmd,size=image.unpack('<II',offset)
        if cmd==2:
            if size<24 or sym is not None:raise ValueError('Invalid duplicate/truncated symbol table')
            sym=image.unpack('<IIII',offset+8)
        elif cmd==0xb:
            if size<80 or indirect is not None:raise ValueError('Invalid indirect symbol table')
            indirect=image.unpack('<II',offset+56)
        elif cmd in {0xc,0x80000018,0x8000001f,0x80000023}:
            start=image.u32(offset+8)
            if size<24 or not 24<=start<size:raise ValueError('Invalid dylib load command')
            raw=image.data[offset+start:offset+size];end=raw.find(b'\0')
            if end<0:raise ValueError('Unterminated dylib name')
            libraries.append(raw[:end].decode('utf-8'))
        offset+=size
    if sym is None or indirect is None:raise ValueError('Missing native linkage tables')
    symoff,nsyms,stroff,strsize=sym;indoff,nind=indirect
    if symoff+16*nsyms>len(image.data) or stroff+strsize>len(image.data) or indoff+4*nind>len(image.data):raise ValueError('Native linkage tables outside image')
    return sym,indirect,libraries


def index(image,section,address,stride,indirect):
    base=section['address'];delta=address-base
    if stride<=0 or delta<0 or delta%stride or delta+stride>section['size']:raise ValueError('Misaligned/outside symbol slot')
    slot=section['reserved1']+delta//stride;offset,count=indirect
    if slot>=count:raise ValueError('Indirect symbol slot outside table')
    value=image.u32(offset+4*slot)
    if value&0xc0000000:raise ValueError('Local/absolute indirect symbol is not an import')
    return value


def inspect(text,image,address,expected_symbol,expected_library):
    code=instructions(text)
    if set(code)!=set(range(address,address+12,4)):raise ValueError('Exact three-instruction native stub required')
    words=[]
    for site in range(address,address+12,4):
        word=code[site][2];off=image.file_offset(site)
        if image.file_offset(site+3)!=off+3 or image.data[off:off+4]!=struct.pack('<I',word):raise ValueError('Stub mapped bytes mismatch')
        words.append(word)
    page,load,branch=words
    if page&0x9f00001f!=0x90000010 or load&0xffc003ff!=0xf9400210 or branch!=0xd61f0200:raise ValueError('Native stub addressing changed')
    pointer=pc_relative(page,address,True)+((load>>10)&4095)*8
    stubs=[s for s in image.sections if s['flags']&255==8 and s['address']<=address< s['address']+s['size']]
    pointers=[s for s in image.sections if s['flags']&255 in {6,7} and s['address']<=pointer<s['address']+s['size']]
    if len(stubs)!=1 or len(pointers)!=1 or stubs[0]['reserved2']!=12:raise ValueError('Unknown native stub/pointer section')
    sym,indirect,libraries=tables(image)
    symbol_index=index(image,stubs[0],address,12,indirect)
    if index(image,pointers[0],pointer,8,indirect)!=symbol_index:raise ValueError('Stub and pointer imports disagree')
    symoff,count,stroff,size=sym
    if symbol_index>=count:raise ValueError('Symbol outside table')
    nameoff,kind,section,description,value=image.unpack('<IBBHQ',symoff+16*symbol_index)
    if nameoff>=size or kind&0xe or not kind&1 or section!=0 or value!=0:raise ValueError('Expected undefined external import')
    raw=image.data[stroff+nameoff:stroff+size];end=raw.find(b'\0')
    if end<0 or raw[:end].decode('utf-8')!=expected_symbol:raise ValueError('Native import name mismatch')
    ordinal=description>>8
    if not 1<=ordinal<=len(libraries) or libraries[ordinal-1]!=expected_library:raise ValueError('Native import library mismatch')
    return {'release_symbol_binding_verified':True,'stub_instruction_bytes_compared':12,'import_symbol':expected_symbol,'import_library':expected_library,'import_pointer_address':hex(pointer),'scope':'Static Mach-O import binding only; dyld interposition, runtime implementation and deallocation remain unobserved.'}
