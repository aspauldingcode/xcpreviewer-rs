"""Static token-state type record identity with symbolic and chained references."""
import struct
import re
from reloop.chained import rebase
from reloop.discriminants import instructions,pc_relative
from reloop.tokenlink import branch


def span(image,address,size):
    if size<=0 or size>512:raise ValueError('Bounded descriptor span required')
    off=image.file_offset(address)
    if image.file_offset(address+size-1)!=off+size-1:raise ValueError('Descriptor span crosses mapping')
    return image.data[off:off+size]


def symbolic(image,address,length):
    raw=span(image,address,length+1)
    if raw[-1]!=0:raise ValueError('Type record lacks length-delimited terminator')
    refs=[];operators=[];i=0
    while i<length:
        byte=raw[i]
        if byte in {1,2}:
            if i+5>length:raise ValueError('Truncated symbolic relative reference')
            target=address+i+1+struct.unpack_from('<i',raw,i+1)[0]
            slot=None
            if byte==2:slot=target;target=rebase(image,slot)['target']
            context=image.context(target)
            if not isinstance(context['name'],str):raise ValueError('Unresolved symbolic context name')
            parents=[];node=context
            while node:
                if not isinstance(node.get('name'),str) or 'parent_unresolved' in node:raise ValueError('Unresolved symbolic parent')
                parents.append(node['name']);node=node.get('parent')
            refs.append({'context_path':list(reversed(parents)),'record_offset':i,'kind':byte,'slot':hex(slot) if slot is not None else None,'descriptor':hex(target),'name':context['name'],'context_kind':context['kind']});i+=5
        elif 32<=byte<127:operators.append(chr(byte));i+=1
        elif byte==255:i+=1
        else:raise ValueError('Unsupported symbolic type operator/reference')
    return {'references':refs,'operators':''.join(operators),'record_bytes':length+1}


def inspect(texts,image):
    bodies={}
    for text in texts:
        code=instructions(text);entry=min(code)
        rows=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
        if len(rows)!=len(set(rows)):raise ValueError('Duplicate wrapper instruction')
        if entry in bodies:raise ValueError('Duplicate token wrapper')
        bodies[entry]=code
    if set(bodies)!={0xbeea8,0xbeecc}:raise ValueError('Two exact token wrappers required')
    records=[]
    for entry,code in sorted(bodies.items()):
        if set(code)!=set(range(entry,entry+36,4)):raise ValueError('Complete bounded wrapper required')
        for site,(_,_,word) in code.items():
            if span(image,site,4)!=struct.pack('<I',word):raise ValueError('Wrapper instruction bytes mismatch')
        pointers=[]
        for site,reg in [(entry+8,3),(entry+16,4)]:
            word=code[site][2];add=code[site+4][2]
            if word&0x9f00001f!=0x90000000|reg or add&0xffc003ff!=0x91000000|(reg<<5)|reg:raise ValueError('Wrapper pointer form changed')
            pointers.append(pc_relative(word,site,True)+((add>>10)&4095))
        if branch(code[entry+24][2],entry+24,True)!=0xbeef0:raise ValueError('Wrapper update call changed')
        cache,descriptor=pointers
        if span(image,cache,8)!=b'\0'*8:raise ValueError('Pinned on-disk metadata cache changed')
        delta,length=struct.unpack('<ii',span(image,descriptor,8))
        if length!=30:raise ValueError('Pinned type record length changed')
        record=symbolic(image,descriptor+delta,length)
        expected=['State','ObserverAndTokenStorage','ConcurrentInvalidationObserverBox','ConcurrentTokenCallback','InvalidationTrace'] if entry==0xbeea8 else ['State','ObserverAndTokenStorage','IsolatedInvalidationObserverBox','IsolatedTokenCallback','InvalidationTrace']
        if any(r['context_path'][0]!='PreviewsFoundationHost' or r['context_kind']!=(18 if i==0 else 17) for i,r in enumerate(record['references'])):raise ValueError('Wrong nominal module or kind')
        if [r['name'] for r in record['references']]!=expected or record['references'][0]['context_path']!=['PreviewsFoundationHost','FulfillOnceState','State'] or record['operators']!='yyG_G':raise ValueError('Token-state symbolic identity changed')
        records.append({'wrapper':hex(entry),'cache':hex(cache),'type_record_descriptor':hex(descriptor),'type_record':hex(descriptor+delta),**record})
    return {'token_descriptors_verified':True,'wrapper_instruction_bytes_compared':72,'record_span_bytes_checked':62,'symbolic_reference_count':10,'zero_disk_cache_bytes_checked':16,'records':records,'scope':'On-disk wrapper association, symbolic nominal references and chained rebase identities only. Actual dyld slide/binding, resolved runtime metadata, concrete value-witness targets/effects, payload ownership and transport remain unobserved.'}
