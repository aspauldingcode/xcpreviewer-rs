"""Static storage/trace bridge delegation; owned model is not runtime release proof."""
import itertools
import struct
from reloop.discriminants import instructions
from reloop.statepattern import checked_body
from reloop.chained import rebase
from reloop.tokendescriptor import span
from reloop.tokenlink import branch
from reloop.stubbind import inspect as inspect_stub

BODIES={
 0x42358:(0x423dc,'7c2a6414bc725de2a61b0376e9b2746e52c2e875b1b710865dbdb521dee43fd4'),
 0x42900:(0x42904,'62ae959a4afb226da5b1feaf9bcd03118b41415dbb2b7f3ac703084878478651'),
 0xdbc0:(0xdbc8,'f5489913dc1ed38547b1eb9b2ef0693a00baa3d209743af5aec2b59a47f870cb'),
 0xed44:(0xed48,'96a9de7c79f7b20f94af4e4de22e945d7599d416472594816b95aee4f9656da2'),
 0xdb94:(0xdbc0,'e3ecc24716147627323bb09a0ac396980ed5829475548f920482771618a21f50')
}


def field_names(image,descriptor):
    fields=image.relative(descriptor+16)
    if fields is None:raise ValueError('Missing ownership reflection descriptor')
    kind,size,count=struct.unpack('<HHI',span(image,fields+8,8))
    if kind!=0 or size!=12 or not 1<=count<=8:raise ValueError('Unexpected bounded struct field records')
    names=[]
    for i in range(count):
        target=image.relative(fields+16+i*size+8)
        if target is None:raise ValueError('Missing reflected field name')
        value=image.string(target)
        if not isinstance(value,str):raise ValueError('Unresolved field name')
        names.append(value)
    return names


def project(source,operation):
    if len(source) not in {8,24} or operation not in {'copy','destroy'}:raise ValueError('One/three-word ownership projection only')
    words=struct.unpack('<'+'Q'*(len(source)//8),source)
    event='bridge_retain' if operation=='copy' else 'bridge_release'
    return {'copied_bytes':bytes(source) if operation=='copy' else None,'events':[(event,word) for word in words]}


def inspect(texts,image):
    bodies={}
    for text in texts:
        start=min(instructions(text))
        if start in bodies:raise ValueError('Duplicate ownership body')
        bodies[start]=text
    if set(bodies)!=set(BODIES)|{0x1311c8,0x1311e0}:raise ValueError('Exact ownership bodies/imports required')
    codes={start:checked_body(bodies[start],image,start,stop,h) for start,(stop,h) in BODIES.items()}
    # Selected load/store/register words receive separate dataflow acceptance.
    selected={0x42358:{0x42368:0xaa0003f3,0x4236c:0xf9400000,0x42374:0xf9400660,0x4237c:0xf9400a60,0x4239c:0xaa0003f3,0x423a0:0x3dc00020,0x423a4:0x3d800000,0x423a8:0xa940d434,0x423ac:0xf9000815,0x423b0:0x9e660000,0x423b8:0xaa1403e0,0x423c0:0xaa1503e0},0xdbc0:{0xdbc0:0xf9400000},0xdb94:{0xdba0:0xaa0003f3,0xdba4:0xf9400020,0xdba8:0xf9000260}}
    for start,sites in selected.items():
        if any(codes[start][site][2]!=word for site,word in sites.items()):raise ValueError('Ownership delegation dataflow changed')
    for start,sites,link in [(0x42358,{0x42370:0x1311c8,0x42378:0x1311c8,0x423b4:0x1311e0,0x423bc:0x1311e0,0x423c4:0x1311e0},True),(0x42358,{0x42358:0x4238c,0x42388:0x1311c8},False),(0x42900,{0x42900:0x42358},False),(0xdbc0,{0xdbc4:0x1311c8},False),(0xed44,{0xed44:0xdb94},False),(0xdb94,{0xdbac:0x1311e0},True)]:
        for site,target in sites.items():
            if branch(codes[start][site][2],site,link)!=target:raise ValueError('Ownership direct delegation changed')
    storage=0x151358;trace=0x1520e0
    if image.context(storage)['name']!='ObserverAndTokenStorage' or image.context(trace)['name']!='InvalidationTrace':raise ValueError('Wrong ownership nominal contexts')
    if image.relative(storage+32)!=0x135478 or span(image,0x135478,16)!=struct.pack('<iiIi',0xcb18-0x135478,0,0x40000001,0x1756d0-0x135484):raise ValueError('Storage generic witness pattern changed')
    if rebase(image,0x179330)['target']!=0x1792d0 or rebase(image,0x179340)['target']!=trace or struct.unpack('<Q',span(image,0x179338,8))[0]!=512:raise ValueError('Trace static struct metadata association changed')
    for table,targets,size in [(0x1756d0,[0x42900,0x4235c,0x42900],24),(0x1792d0,[0xed44,0xdbc0,0xed44],8)]:
        if [rebase(image,table+8*i)['target'] for i in range(3)]!=targets or span(image,table+64,16)!=struct.pack('<QQ',size,size):raise ValueError('Ownership witness slots or size/stride changed')
    fields={ 'storage':field_names(image,storage),'trace':field_names(image,trace)}
    if fields!={'storage':['observers','managedTokens'],'trace':['links']}:raise ValueError('Ownership reflection names changed')
    for address,name in [(0x1311c8,'_swift_bridgeObjectRelease'),(0x1311e0,'_swift_bridgeObjectRetain')]:inspect_stub(bodies[address],image,address,name,'/usr/lib/swift/libswiftCore.dylib')
    cases=0;compared=0;values=[0,1,0xffffffffffffffff,0x8000000000000000,0x0123456789abcdef]
    for count in [1,3]:
        for words in itertools.product(values,repeat=count):
            source=b''.join(word.to_bytes(8,'little') for word in words)
            copied=project(source,'copy');destroyed=project(source,'destroy')
            if copied['copied_bytes']!=source or copied['events']!=[('bridge_retain',v) for v in words] or destroyed['events']!=[('bridge_release',v) for v in words]:raise ValueError('Owned delegation model contradicts byte/word oracle')
            compared+=len(source);cases+=1
    return {'storage_ownership_verified':True,'body_instruction_bytes_compared':192,'import_instruction_bytes_compared':24,'ownership_model_cases':cases,'owned_model_bytes_compared':compared,'storage_bridge_calls_per_operation':3,'trace_bridge_calls_per_operation':1,'storage_value_bytes':24,'trace_value_bytes':8,'reflected_fields':fields,'scope':'Static generic storage pattern/static trace metadata, declared witness/import delegation and owned finite model only. Null/alias arguments remain distinct calls, not proof of distinct allocations, actual runtime retains/releases, reclamation, state races or Canvas cleanup.'}
