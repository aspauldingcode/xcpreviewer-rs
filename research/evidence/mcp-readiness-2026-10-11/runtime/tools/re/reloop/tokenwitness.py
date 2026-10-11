"""Pinned byte-level witness dispatch and metadata-cache gate; no runtime effects."""
import re
import struct
from reloop.discriminants import instructions
from reloop.tokenlink import branch
from reloop.stubbind import inspect as inspect_stub

# Independent acceptance words for the complete bounded bodies, including frames.
WORDS={
 0xebc8:[0xa9be4ff4,0xa9017bfd,0x910043fd,0xaa0103f3,0xaa0003f4,0xaa0203e0,0xaa0303e1,0x97ffcecb,0xaa0003e2,0xf85f8008,0xf9400908,0xaa1303e0,0xaa1403e1,0xd63f0100,0xaa1303e0,0xa9417bfd,0xa8c24ff4,0xd65f03c0],
 0x41dc:[0xa9be4ff4,0xa9017bfd,0x910043fd,0xaa0003f3,0xaa0103e0,0xaa0203e1,0x97fff947,0xaa0003e1,0xf85f8008,0xf9400508,0xaa1303e0,0xd63f0100,0xaa1303e0,0xa9417bfd,0xa8c24ff4,0xd65f03c0],
 0x2710:[0xa9be4ff4,0xa9017bfd,0x910043fd,0xaa0003f3,0xf9400000,0x92400008,0xf100001f,0xfa401900,0x54000120,0xf9400029,0x9360fd28,0x8b29c020,0xaa0803e1,0xd2800002,0xd2800003,0x9404bb1a,0xf9000260,0xa9417bfd,0xa8c24ff4,0xd65f03c0]
}


def checked(text,image,start,count):
    code=instructions(text)
    rows=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
    if len(rows)!=len(set(rows)) or set(code)!=set(range(start,start+count*4,4)):raise ValueError('Exact witness body instructions required')
    words=[]
    for site in sorted(code):
        word=code[site][2];off=image.file_offset(site)
        if image.file_offset(site+3)!=off+3 or image.data[off:off+4]!=struct.pack('<I',word):raise ValueError('Witness mapped bytes mismatch')
        words.append(word)
    return words


def cache_projection(value):
    value&=(1<<64)-1
    # CMP sets Z for zero. CCMP executes only when CMP is NE; otherwise NZCV=0.
    zero=value==0
    z=((value&1)==0) if not zero else False
    return not z


def inspect(texts,image):
    bodies={}
    for text in texts:
        start=min(instructions(text))
        if start in bodies:raise ValueError('Duplicate witness entry')
        bodies[start]=text
    if set(bodies)!=set(WORDS)|{0x1313b4}:raise ValueError('Exact witness/resolver/import entries required')
    for start,expected in WORDS.items():
        if checked(bodies[start],image,start,len(expected))!=expected:raise ValueError('Witness dispatch or resolver body changed')
    # Encoded direct calls; import annotations do not supply target identity.
    for site,word,target in [(0xebe4,WORDS[0xebc8][7],0x2710),(0x41f4,WORDS[0x41dc][6],0x2710),(0x274c,WORDS[0x2710][15],0x1313b4)]:
        if branch(word,site,True)!=target:raise ValueError('Witness metadata call changed')
    values=list(range(65536))+[1<<63,(1<<63)+1,(1<<64)-2,(1<<64)-1]
    for value in values:
        if cache_projection(value)!=(value==0 or value%2==1):raise ValueError('Metadata cache gate contradicts independent oracle')
    binding=inspect_stub(bodies[0x1313b4],image,0x1313b4,'_swift_getTypeByMangledNameInContext2','/usr/lib/swift/libswiftCore.dylib')
    return {'witness_dispatch_verified':True,'compared_witness_instruction_bytes':216,'metadata_stub_instruction_bytes_compared':binding['stub_instruction_bytes_compared'],'metadata_import_symbol':binding['import_symbol'],'metadata_import_library':binding['import_library'],'metadata_import_pointer':binding['import_pointer_address'],'metadata_cache_cases':len(values),'copy_table_slot_bytes':16,'destroy_table_slot_bytes':8,'metadata_runtime_gate':'cached_word==0 or low_bit==1','scope':'Static complete helper bodies and declared import binding only. Runtime type resolution, witness target identity/effects, retained payload ownership, native calls, races, transport cleanup and reclamation remain unobserved.'}
