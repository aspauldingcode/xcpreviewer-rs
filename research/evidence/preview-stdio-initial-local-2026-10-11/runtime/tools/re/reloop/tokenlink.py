"""Pinned static capture-to-removal association; no runtime invocation claim."""
import re
import struct
from reloop.discriminants import instructions,pc_relative

SITES={
 0xc1210:{0xc1210:('ldp','x0, x1, [x20, #0x10]')},
 0xc12f8:{0xc12f8:('ldp','x0, x1, [x20, #0x10]')},
 0x419cc:{},0x41f10:{},
 0x41f2c:{0x41f44:('mov','x19, x4'),0x41f48:('mov','x20, x3'),0x41f4c:('mov','x21, x2'),0x41f50:('mov','x22, x1'),0x41f54:('mov','x23, x0'),0x41f6c:('add','x0, x23, #0x10'),0x41f74:('cbz','x0, 0x41fc4'),0x41f78:('ldr','x8, [x0, #0x20]'),0x41f7c:('str','x22, [sp, #0x20]'),0x41f80:('ldr','x23, [x8, #0x98]'),0x41f88:('add','x0, x23, #0x54'),0x41f94:('add','x0, x23, #0x10'),0x41f98:('add','x2, sp, #0x10'),0x41f9c:('mov','x1, x21'),0x41fa4:('blr','x20'),0x41fa8:('add','x0, x23, #0x54'),0x41fc0:('blr','x19')},
 0xbeea8:{},0xbeecc:{},
 0xbeef0:{0xbef20:('ldrh','w8, [x0, #0x40]'),0xbef3c:('ubfx','w8, w8, #8, #8'),0xbef40:('cmp','w8, #0x1'),0xbef44:('b.ne','0xbef68'),0xbef60:('mov','w8, #0x1'),0xbef68:('mov','x24, x2'),0xbef6c:('mov','x23, x1'),0xbefb8:('str','x26, [sp, #0x10]'),0xbefc4:('add','x0, sp, #0x10'),0xbefc8:('mov','x8, x22'),0xbefcc:('mov','x20, x24'),0xbefd0:('blr','x23'),0xbefd4:('mov','w8, #0x0'),0xbefe0:('str','q0, [x27]'),0xbefe4:('str','x9, [x27, #0x10]'),0xbefe8:('strb','wzr, [x27, #0x41]'),0xbefec:('strb','w8, [x22, #0x8]')},
 0x428fc:{},0x42104:{}
}
BRANCHES={0xc1210:{0xc1214:0x419cc},0xc12f8:{0xc12fc:0x41f10},0x419cc:{0x419e4:0x41f2c},0x41f10:{0x41f28:0x41f2c},0x428fc:{0x428fc:0x42648},0xbeef0:{0xbef64:0xbefec}}
CALLS={0x41f2c:{0x41f68:0x1311bc,0x41f70:0x13166c,0x41f8c:0x131120,0x41fac:0x13112c,0x41fb4:0x131498},0xbeea8:{0xbeec0:0xbeef0},0xbeecc:{0xbeee4:0xbeef0}}
POINTERS={0x419cc:[(0x419cc,2,0x42604),(0x419d4,3,0xbeecc),(0x419dc,4,0x428fc)],0x41f10:[(0x41f10,2,0x428d0),(0x41f18,3,0xbeea8),(0x41f20,4,0x428fc)]}


def branch(word,site,link):
    if word>>26!=(0x25 if link else 0x5):raise ValueError('Wrong encoded direct branch')
    imm=word&0x3ffffff
    if imm&0x2000000:imm-=0x4000000
    return site+4*imm


def inspect(texts,image):
    codes={};compared=0
    for text in texts:
        code={site:(op,re.sub(r'\s+<[^>]*>$','',args),word) for site,(op,args,word) in instructions(text).items()}
        if not code or min(code) in codes:raise ValueError('Missing/duplicate token-link entry')
        rows=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
        if len(rows)!=len(set(rows)):raise ValueError('Duplicate token-link instruction')
        for site,(_,_,word) in code.items():
            off=image.file_offset(site)
            if image.file_offset(site+3)!=off+3 or image.data[off:off+4]!=struct.pack('<I',word):raise ValueError('Mapped token-link bytes changed')
            compared+=4
        codes[min(code)]=code
    if set(codes)!=set(SITES):raise ValueError('Exact ten token-link entries required')
    for entry,sites in SITES.items():
        if any(codes[entry].get(site,())[:2]!=pair for site,pair in sites.items()):raise ValueError('Token capture/update dataflow changed')
    for entries,link in [(BRANCHES,False),(CALLS,True)]:
        for entry,sites in entries.items():
            for site,target in sites.items():
                if site not in codes[entry] or branch(codes[entry][site][2],site,link)!=target:raise ValueError('Token-link branch target changed')
    for entry,items in POINTERS.items():
        for site,reg,target in items:
            code=codes[entry];word=code[site][2];add=code[site+4][2]
            if word&0x9f00001f!=0x90000000|reg or add&0xffc003ff!=0x91000000|(reg<<5)|reg:raise ValueError('Token pointer register/immediate form changed')
            if pc_relative(word,site,True)+((add>>10)&0xfff)!=target:raise ValueError('Token pointer target changed')
    null=codes[0x41f2c][0x41f74][2]
    if null&0xff00001f!=0xb4000000 or 0x41f74+4*((null>>5)&0x7ffff)!=0x41fc4:raise ValueError('Weak-owner null guard changed')
    guard=codes[0xbeef0][0xbef44][2]
    if guard&0xff00001f!=0x54000001 or 0xbef44+4*((guard>>5)&0x7ffff)!=0xbef68:raise ValueError('State guard branch changed')
    return {'token_link_verified':True,'entry_count':len(codes),'compared_instruction_bytes':compared,'captured_pointer_targets':6,'encoded_direct_targets':13,'weak_owner_skip':True,'state_high_byte_one_skips_callback':True,'capture_key_context_offset':16,'scope':'Static captured-pointer and selected dataflow association only; runtime invocation, enum names, value-witness effects, dictionary contents, races, transport cleanup and final reclamation remain open.'}
