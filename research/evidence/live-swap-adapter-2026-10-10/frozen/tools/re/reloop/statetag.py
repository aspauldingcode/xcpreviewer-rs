"""Static State case indices and direct-tag0/1 model; no runtime enum calls."""
import struct
from reloop.stubbind import tables
from reloop.discriminants import instructions
from reloop.statepattern import checked_body
from reloop.chained import rebase
from reloop.tokendescriptor import span
from reloop.tokenconsume import signed
from reloop.tokenlink import branch

SYMBOLS={
 'waiting':('_$s22PreviewsFoundationHost16FulfillOnceStateC0F0O7waitingyAEyxq__Gx_tcAGmr0_lFWC',0x1341d0,0),
 'fulfilled':('_$s22PreviewsFoundationHost16FulfillOnceStateC0F0O9fulfilledyAEyxq__Gq__AA8CallsiteVtcAGmr0_lFWC',0x1341d4,1)
}
BODIES={
 0x1e5c:(0x1e60,'110f46b5b35c069160560c6ad6786f647dd44e8760a52a46fc22dbbcd7630b91'),
 0x2dcf8:(0x2dd9c,'939e052cd0a6e8e551d50220cb230ae4d7df4339a7744b401e748424f192ff00'),
 0x2dd9c:(0x2de9c,'c09280b71a394cd07e4b5b6127beb126dcde890cd1e301553a3b972b7d61c55a')
}


def defined_symbol(image,name,address):
    (symoff,count,stroff,size),_,_=tables(image)
    if count>2000000:raise ValueError('Symbol inventory bound')
    matches=[]
    for i in range(count):
        start,kind,section,description,value=image.unpack('<IBBHQ',symoff+16*i)
        if start>=size:raise ValueError('Symbol name outside table')
        end=image.data.find(b'\0',stroff+start,stroff+size)
        if end<0:raise ValueError('Unterminated symbol name')
        if image.data[stroff+start:end]!=name.encode():continue
        if kind&0xe0 or kind&0xe!=0xe or not 1<=section<=len(image.sections) or value!=address:raise ValueError('Expected unique defined section symbol')
        s=image.sections[section-1]
        if not s['disk'] or not s['address']<=value or value+4>s['address']+s['size']:raise ValueError('Case symbol outside file-backed section')
        matches.append(i)
    if len(matches)!=1:raise ValueError('Missing/duplicate defined case symbol')
    return matches[0]


def tag_offset(a,b):
    if type(a) is not int or type(b) is not int or not 0<=a<=4096 or not 0<=b<=4096:raise ValueError('Bounded direct-tag layout sizes')
    return max(a,((b+7)&~7)+57)


def inject(source,a,b,tag):
    if type(tag) is not int or tag not in {0,1}:raise ValueError('Only direct State tags0/1 accepted')
    offset=tag_offset(a,b)
    if len(source)<=offset:raise ValueError('Missing tag byte')
    result=bytearray(source);result[offset]=tag
    return bytes(result)


def get_tag(source,a,b):
    offset=tag_offset(a,b)
    if len(source)<=offset or source[offset] not in {0,1}:raise ValueError('Only direct State tag-byte domain')
    return source[offset]


def inspect(texts,image):
    bodies={}
    for text in texts:
        start=min(instructions(text))
        if start in bodies:raise ValueError('Duplicate State tag body')
        bodies[start]=text
    if set(bodies)!=set(BODIES):raise ValueError('Exact State tag bodies required')
    codes={start:checked_body(bodies[start],image,start,stop,h) for start,(stop,h) in BODIES.items()}
    if [rebase(image,0x173f70+8*i)['target'] for i in range(3)]!=[0x2dcf8,0x1e5c,0x2dd9c]:raise ValueError('Enum witness slots changed')
    if span(image,0x1341d0,8)!=struct.pack('<II',0,1):raise ValueError('Independent named case-index bytes changed')
    for name,address,index in SYMBOLS.values():defined_symbol(image,name,address)
    d=0x1508f8;ctx=image.context(d)
    if ctx['kind']!=18 or ctx['name']!='State' or ctx.get('parent',{}).get('name')!='FulfillOnceState':raise ValueError('Wrong State case context')
    f=image.relative(d+16)
    if struct.unpack('<HHI',span(image,f+8,8))!=(2,12,2):raise ValueError('Wrong State enum field record bounds')
    names=[image.string(image.relative(f+16+12*i+8)) for i in range(2)]
    if names!=['waiting','fulfilled']:raise ValueError('State reflected case names changed')
    selected={0x2dcf8:{0x2dcf8:0xa9412428,0x2dd20:0x38696808,0x2dd24:0x7100090a,0x2dd94:0xaa0803e0,0x2dd98:0xd65f03c0},0x2dd9c:{0x2ddac:0x7100043f,0x2ddb4:0xa9412049,0x2dddc:0x38286801},0x1e5c:{0x1e5c:0xd65f03c0}}
    for start,sites in selected.items():
        if any(codes[start][site][2]!=word for site,word in sites.items()):raise ValueError('State direct-tag dataflow changed')
    for start,site,target,condition in [(0x2dcf8,0x2dd28,0x2dd94,3),(0x2dd9c,0x2ddb0,0x2dde4,8)]:
        w=codes[start][site][2]
        if w&0xff00001f!=0x54000000|condition or site+4*signed((w>>5)&0x7ffff,19)!=target:raise ValueError('State direct-tag branch changed')
    if branch(codes[0x2dd9c][0x2dde0][2],0x2dde0,False)!=0x2de8c:raise ValueError('State direct injector exit changed')
    cases=0;compared=0
    for a in range(257):
        for b in range(257):
            offset=max(a,8*((b+7)//8)+57);source=bytes([0xa5])*(offset+5)
            for tag in [0,1]:
                actual=inject(source,a,b,tag);expected=source[:offset]+bytes([tag])+source[offset+1:]
                if actual!=expected or get_tag(actual,a,b)!=tag:raise ValueError('State inject/get projection contradicts byte/padding oracle')
                compared+=len(actual);cases+=1
    return {'state_tags_verified':True,'body_instruction_bytes_compared':424,'case_index_bytes_independently_compared':8,'enum_witness_rebases_verified':3,'named_case_indices':{'waiting':0,'fulfilled':1},'direct_tag_buffer_cases':cases,'whole_buffer_model_bytes_compared':compared,'padding_bytes_per_model_buffer':4,'scope':'Static named resilient case indices, reflected enum declarations and declared witness bodies; finite direct-tag models only. WaitingStateUpdateResult uses a separate discriminator. No live State value, generic metadata construction, native getter/injector execution, extended-tag validity, race or transport claim.'}
