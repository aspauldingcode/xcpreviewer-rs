"""Pinned generic State pattern and finite direct-tag witness projection."""
import hashlib
import re
import struct
from reloop.discriminants import instructions
from reloop.tokendescriptor import span
from reloop.chained import rebase
from reloop.tokenlink import branch
from reloop.stubbind import inspect as inspect_stub

BODIES={
 0xec10:(0xec18,'2d694f6af8958aaed74eb4ef571382b8c47897068dee0ff4d3e5dec90cf025c0'),
 0x2d148:(0x2d1e4,'465120595f30dc065b1f899d53b9d22832a1706d9b5a80bcf4c0dc24e116c5a2'),
 0x2d360:(0x2d410,'f78789e220ac604390f1a896d5dc21f2b9421699daf85a89f5e6cff3bcdf3fd8'),
 0x2d410:(0x2d544,'5c6b92aba74acf243673150f479b9d0f88fa66edbfc34c5da09afab2700ae522')
}
# Complete reviewed body fingerprints are identity checks, not independent semantic oracles.
IMPORTS={0x131180:'_swift_allocateGenericValueMetadata',0x1311f8:'_swift_checkMetadataState',0x131378:'_swift_getTupleTypeLayout2',0x1313e4:'_swift_initEnumMetadataMultiPayload'}


def checked_body(text,image,start,stop,expected_hash):
    code=instructions(text);rows=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
    if len(rows)!=len(set(rows)) or set(code)!=set(range(start,stop,4)):raise ValueError('Exact bounded State witness body required')
    raw=b''.join(struct.pack('<I',code[site][2]) for site in range(start,stop,4))
    if raw!=span_bytes(image,start,stop-start):raise ValueError('State body mapped bytes mismatch')
    if hashlib.sha256(raw).hexdigest()!=expected_hash:raise ValueError('Reviewed State body identity changed')
    return code


def span_bytes(image,address,size):
    off=image.file_offset(address)
    if size<=0 or size>4096 or image.file_offset(address+size-1)!=off+size-1:raise ValueError('State body mapping bounds')
    return image.data[off:off+size]


def layout_projection(size_a,size_b,tag):
    if type(size_a) is not int or type(size_b) is not int or not 0<=size_a<=4096 or not 0<=size_b<=4096 or tag not in {0,1}:raise ValueError('Direct-tag projection domain')
    extent=max(size_a,((size_b+7)&~7)+57)
    return {'tag_offset':extent,'payload_index':1 if tag==1 else 0,'copies_trailer':tag==1}


def copy_trailer(source):
    if len(source)!=57:raise ValueError('Exact 57-byte projected trailer required')
    destination=bytearray(57)
    destination[41:57]=source[41:57]
    destination[16:48]=source[16:48]
    destination[0:16]=source[0:16]
    return bytes(destination)


def inspect(texts,image):
    bodies={}
    for text in texts:
        entry=min(instructions(text))
        if entry in bodies:raise ValueError('Duplicate State entry')
        bodies[entry]=text
    if set(bodies)!=set(BODIES)|set(IMPORTS):raise ValueError('Exact State pattern body/import set required')
    descriptor=0x1508f8
    ctx=image.context(descriptor)
    if ctx['kind']!=18 or ctx['name']!='State' or ctx.get('parent',{}).get('name')!='FulfillOnceState':raise ValueError('Wrong State nominal context')
    flags,parent,name,access,fields,payload,empty,cache,pattern,counts,keys,params=struct.unpack('<12I',span(image,descriptor,48))
    if flags!=0xd2 or payload!=0x04000002 or empty!=0 or counts!=2 or keys!=2 or params!=0x8080:raise ValueError('State generic header changed')
    if image.relative(descriptor+12)!=0x2cfc8 or image.relative(descriptor+28)!=0x1878c0 or image.relative(descriptor+32)!=0x1341c0:raise ValueError('State descriptor link changed')
    p=0x1341c0;expected=struct.pack('<iiIi',0xec10-p,0x2d148-(p+4),0x40200000,0x173f18-(p+12))
    if span(image,p,16)!=expected:raise ValueError('Independent State pattern bytes changed')
    table=0x173f18;targets=[rebase(image,table+8*i)['target'] for i in range(8)]
    if targets!=[0x2d1e4,0x2d360,0x2d410,0x2d544,0x2d720,0x2d854,0x2da30,0x2db44]:raise ValueError('State witness table target changed')
    codes={start:checked_body(bodies[start],image,start,stop,h) for start,(stop,h) in BODIES.items()}
    for site,target,link in [(0xec14,0x131180,False),(0x2d164,0x1311f8,True),(0x2d184,0x1311f8,True),(0x2d1a8,0x131378,True),(0x2d1c0,0x1313e4,True)]:
        code=codes[0xec10 if site<0x10000 else 0x2d148]
        if branch(code[site][2],site,link)!=target:raise ValueError('State runtime branch changed')
    for address,name in IMPORTS.items():inspect_stub(bodies[address],image,address,name,'/usr/lib/swift/libswiftCore.dylib')
    cases=0
    for a in range(257):
        for b in range(257):
            for tag in [0,1]:
                actual=layout_projection(a,b,tag);extent=max(a,((b+7)//8)*8+57)
                if actual!={'tag_offset':extent,'payload_index':tag,'copies_trailer':bool(tag)}:raise ValueError('State layout projection contradicts independent expectations')
                cases+=1
    source=bytes((i*37+19)%256 for i in range(57))
    if copy_trailer(source)!=source:raise ValueError('Projected overlapping trailer copy loses bytes')
    return {'state_pattern_verified':True,'body_instruction_bytes_compared':648,'import_instruction_bytes_compared':48,'independently_predicted_pattern_bytes':16,'generic_descriptor_bytes_checked':48,'witness_rebases_verified':8,'destroy_target':'0x2d360','copy_target':'0x2d410','direct_tag_layout_cases':cases,'trailer_copy_bytes_compared':57,'numeric_tag_offset':'max(sizeA, align8(sizeB)+57)','imports':list(IMPORTS.values()),'scope':'Static generic pattern and declared witness targets; finite direct-tag0/1 and trailer-copy projections. No runtime instantiation, actual witness invocation, extended-tag acceptance, payload ownership, release counts, races or Canvas transport proof.'}
