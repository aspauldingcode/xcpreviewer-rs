"""Bounded on-disk DYLD_CHAINED_PTR_64_OFFSET rebases; never runtime pointers."""


def rebase(image,address):
    offset=32;segments=[];payload=None
    for _ in range(image.u32(16)):
        cmd,size=image.unpack('<II',offset)
        if cmd==0x19:
            vm,extent,fileoff,filesize=image.unpack('<QQQQ',offset+24)
            segments.append((vm,extent,fileoff,filesize))
        if cmd==0x80000034:
            if payload is not None or size!=16:raise ValueError('Invalid chained fixup command')
            payload=image.unpack('<II',offset+8)
        offset+=size
    if payload is None:raise ValueError('Missing chained fixups')
    base,length=payload
    if length<28 or base+length>len(image.data):raise ValueError('Fixup payload outside image')
    def read(fmt,relative):
        import struct
        if relative<0 or relative+struct.calcsize(fmt)>length:raise ValueError('Fixup metadata outside payload')
        return image.unpack(fmt,base+relative)
    version,starts,*_=read('<7I',0)
    if version!=0:raise ValueError('Unsupported fixups version')
    count=read('<I',starts)[0]
    if count!=len(segments) or count>128:raise ValueError('Fixup segment count mismatch')
    candidates=[(i,s) for i,s in enumerate(segments) if s[0]<=address<s[0]+s[1]]
    if len(candidates)!=1:raise ValueError('Ambiguous fixup address')
    i,(vm,extent,fileoff,filesize)=candidates[0]
    imagebase=min(s[0] for s in segments if s[3] and s[2]==0)
    relative=read('<I',starts+4+4*i)[0]
    if relative==0:raise ValueError('Segment has no fixup starts')
    entry=starts+relative
    size,page,kind,segoff,maximum,pages=read('<IHHQIH',entry)
    if size<22+2*pages or entry+size>length or page not in {4096,16384} or kind!=6 or maximum!=0 or vm!=imagebase+segoff:raise ValueError('Unsupported/inconsistent fixup segment')
    index=(address-vm)//page
    if index>=pages:raise ValueError('Fixup page outside starts')
    first=read('<H',entry+22+2*index)[0]
    if first==0xffff or first&0x8000 or first>=page or first%4:raise ValueError('Unsupported/absent page chain')
    origin=vm+index*page;cursor=origin+first
    for hops in range(page//4):
        if not origin<=cursor or cursor+8>min(origin+page,vm+filesize):raise ValueError('Fixup chain outside file-backed page')
        off=fileoff+cursor-vm
        if image.file_offset(cursor)!=off or image.file_offset(cursor+7)!=off+7:raise ValueError('Fixup mapping mismatch')
        word=image.unpack('<Q',off)[0]
        if cursor==address:
            if word>>63 or (word>>44)&127 or (word>>36)&255:raise ValueError('Expected untagged non-bind rebase')
            target=imagebase+(word&((1<<36)-1));image.file_offset(target)
            return {'target':target,'pointer_format':kind,'chain_hops':hops,'slot':address}
        stride=((word>>51)&4095)*4
        if not stride or cursor>address:raise ValueError('Address not a member of the page fixup chain')
        cursor+=stride
    raise ValueError('Fixup chain traversal limit')
