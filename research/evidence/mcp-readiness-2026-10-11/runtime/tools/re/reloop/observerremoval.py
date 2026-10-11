"""Finite pinned observer-removal instruction projection, not native invocation."""
import re
import struct
from reloop.discriminants import instructions,pc_relative

# Selected branch/dataflow sites; surrounding instructions remain in local seals.
SITES={
 0x42604:{0x42618:('ldr','x1, [x20, #0x10]'),0x42620:('ldr','q0, [x9, #0x190]'),0x42624:('str','q0, [sp]'),0x42628:('stp','xzr, xzr, [sp, #0x10]'),0x4262c:('mov','x0, sp')},
 0x428d0:{0x428e0:('ldr','x0, [x20, #0x10]'),0x428e4:('mov','x20, x8')},
 0xedf78:{0xedfb0:('ldp','x8, x9, [sp]'),0xedfb4:('cmp','x8, #0x0'),0xedfb8:('ccmp','x9, #0x1, #0x0, eq'),0xedfbc:('b.eq','0xee018'),0xee03c:('mov','x0, x21'),0xee078:('ret','')},
 0xee75c:{0xee784:('tbz','w1, #0x0, 0xee7ec'),0xee79c:('cbz','w0, 0xee824'),0xee7ac:('ldp','x22, x23, [x8]'),0xee7b8:('str','x20, [x19]'),0xee7bc:('ldr','x9, [x19, #0x8]!'),0xee7d4:('cmp','x10, x21'),0xee7d8:('b.eq','0xee7f8'),0xee7e4:('b.ne','0xee7d0'),0xee7e8:('brk','#0x1'),0xee7ec:('mov','x22, #0x0'),0xee7f0:('mov','x23, #0x0'),0xee7f4:('b','0xee804'),0xee830:('b','0xee7a0')},
 0xee834:{0xee858:('ldp','x8, x9, [sp]'),0xee85c:('cmp','x8, #0x0'),0xee860:('ccmp','x9, #0x1, #0x0, eq'),0xee864:('b.eq','0xee8a4'),0xee88c:('cmp','x10, x21'),0xee890:('b.eq','0xee8d0'),0xee89c:('b.ne','0xee888'),0xee8a0:('brk','#0x1'),0xee8c0:('ldr','q0, [x8, #0x190]'),0xee8c4:('str','q0, [x19]'),0xee8c8:('stp','xzr, xzr, [x19, #0x10]'),0xee8cc:('b','0xee8e4')},
 0x18158:{0x18188:('mov','x25, #-0x1'),0x18298:('lsl','x9, x25, x22'),0x182a0:('sub','x9, x9, #0x1'),0x182a4:('and','x9, x10, x9'),0x182a8:('str','x9, [x21, x8]'),0x182ac:('ldr','x8, [x19, #0x10]'),0x182b0:('subs','x8, x8, #0x1'),0x182b4:('b.vs','0x182e8'),0x182b8:('str','x8, [x19, #0x10]'),0x182bc:('ldr','w8, [x19, #0x24]'),0x182c0:('add','w8, w8, #0x1'),0x182c4:('str','w8, [x19, #0x24]'),0x182e8:('brk','#0x1')},
 0xf82dc:{0xf8304:('tbz','w0, #0x0, 0xf8350'),0xf8308:('ldr','x8, [x19, #0x10]'),0xf830c:('cmp','x21, x8'),0xf8310:('b.hs','0xf8360'),0xf8314:('sub','x23, x8, #0x1'),0xf8318:('add','x0, x19, x21, lsl #3'),0xf831c:('ldr','x8, [x0, #0x20]!'),0xf8320:('str','x8, [x22]'),0xf8324:('sub','x8, x23, x21'),0xf8328:('lsl','x2, x8, #3'),0xf832c:('add','x1, x0, #0x8'),0xf8334:('str','x23, [x19, #0x10]'),0xf8338:('str','x19, [x20]'),0xf835c:('b','0xf8308'),0xf8360:('brk','#0x1')},
}
CALLS={0x42604:{0x42634:0xedf78},0x428d0:{0x428e8:0xee75c},0xedf78:{0xedfd8:0xee23c,0xee040:0xee834},0xee75c:{0xee790:0x131438,0xee7b4:0x18158,0xee800:0xf82dc,0xee828:0x13130},0xee834:{0xee8d4:0xf82dc},0xf82dc:{0xf8300:0x131438,0xf8330:0x13106c,0xf8354:0x3c6bc}}


def inspect(texts,image):
    codes={}
    for text in texts:
        code=instructions(text)
        if not code:raise ValueError('Missing observer-removal instructions')
        entry=min(code);addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
        if entry in codes or len(addresses)!=len(set(addresses)):raise ValueError('Duplicate observer-removal evidence')
        codes[entry]=code
    if set(codes)!=set(SITES):raise ValueError('Exact observer-removal entries required')
    for entry,sites in SITES.items():
        code=codes[entry]
        if any(code.get(p,())[:2]!=value for p,value in sites.items()):raise ValueError('Observer-removal branch/dataflow changed')
        for site,target in CALLS.get(entry,{}).items():
            if site not in code or code[site][0]!='bl':raise ValueError('Missing observer-removal call')
            word=code[site][2]
            if word>>26!=0x25:raise ValueError('Expected encoded BL')
            displacement=word&0x3ffffff
            if displacement&0x2000000:displacement-=0x4000000
            if site+4*displacement!=target:raise ValueError('Observer-removal encoded target changed')
    constants=[]
    for entry,site,reg in [(0x42604,0x4261c,'x9'),(0xee834,0xee8bc,'x8')]:
        code=codes[entry]
        if site not in code or code[site][0]!='adrp' or not code[site][1].startswith(reg+', '):raise ValueError('Sentinel base changed')
        address=pc_relative(code[site][2],site,True)+0x190;offset=image.file_offset(address)
        if image.file_offset(address+15)!=offset+15:raise ValueError('Sentinel crosses mapped extent')
        raw=image.data[offset:offset+16]
        if raw!=struct.pack('<QQ',0,1):raise ValueError('Sentinel full bytes changed')
        constants.append(address)
    if constants!=[0x133190,0x133190]:raise ValueError('Sentinel constant identity changed')
    return {'observer_removal_verified':True,'sentinel_words':[0,1],'sentinel_bytes':16,
            'sentinel_address':hex(constants[0]),'hash_count_decrement':True,'hash_mutation_counter_increment':True,
            'array_count_decrement':True,'ordered_key_missing_traps':True,'encoded_call_targets_verified':sum(map(len,CALLS.values())),
            'scope':'Pinned static instruction projection and full mapped constant only; named Swift ABI tags, value-witness effects, native dictionary contents, callback association, transport cleanup and final reclamation remain unverified.'}
