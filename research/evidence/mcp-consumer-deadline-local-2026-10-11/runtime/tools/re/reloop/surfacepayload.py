"""Static codec keys, corroborated with nominal descriptors; no Swift ABI calls."""
import pathlib
import subprocess
from reloop.core import atomic,digest
from reloop.discriminants import IMAGE,instructions,interpret
from reloop.swiftmeta import MachO,inspect

SYMBOL='_$s21PreviewsMessagingHost16IOSurfacePayloadV3Key33_9EB199A477CFC41B350A6EFBC2D206BELLO0a10FoundationC0012PropertyListF0AagHP8rawValueSSvgTW'
EXPECTED=('surfaceID','scaleFactor','width','height','selectableRegions')
CONTRACTS={
    'IOSurfacePayload':('IOSurfacePayload','Key',EXPECTED,EXPECTED,SYMBOL),
    'RenderPayload':('RenderPayload','Key',('bitmapDescription','selectableRegions','snapshotCornerRadius','scaleFactor'),('bitmapDescription','selectableRegions','snapshotCornerRadius','scaleFactor'),'_$s21PreviewsMessagingHost13RenderPayloadV3Key33_9EB199A477CFC41B350A6EFBC2D206BELLO0a10FoundationC0012PropertyListF0AagHP8rawValueSSvgTW'),
    'BitmapDescription':('BitmapDescription','Key',('data','width','height','bytesPerRow','bitmapInfo','bitsPerComponent','bitsPerPixel','colorSpace'),('data','width','height','bytesPerRow','byteOrder','bitmapInfo','bitsPerComponent','bitsPerPixel','colorSpace'),'_$s21PreviewsMessagingHost17BitmapDescriptionV3Key33_FF1D0E9CDC7C26AC16D452C8D5E8488ELLO0a10FoundationC0012PropertyListF0AagHP8rawValueSSvgTW'),
    'ServiceMessage':('ServiceMessage','Key',('identifier','content'),('messageType','payload'),'_$s21PreviewsMessagingHost14ServiceMessageV3Key33_CC0469B81E19FCEFAC1BFCC0594A0D03LLO0a10FoundationC0012PropertyListF0AagHP8rawValueSSvgTW'),
    'ServiceMessagePayload':('ServiceMessage','PayloadKey',('identifier','content'),('identifier',),'_$s21PreviewsMessagingHost14ServiceMessageV10PayloadKey33_CC0469B81E19FCEFAC1BFCC0594A0D03LLO0a10FoundationC0012PropertyListG0AagHP8rawValueSSvgTW')
}


def has_ancestor(context,name):
    for _ in range(8):
        context=context.get('parent')
        if not isinstance(context,dict):return False
        if context.get('name')==name:return True
    return False


def select(metadata,control="IOSurfacePayload"):
    if control not in CONTRACTS:raise ValueError("Unsupported codec control")
    typename,keyname,expected_fields,expected_keys,_=CONTRACTS[control]
    payloads=[t for t in metadata['types'] if t.get('name')==typename and t.get('kind')==17]
    keys=[t for t in metadata['types'] if t.get('name')==keyname and t.get('kind')==18 and has_ancestor(t,typename)]
    if len(payloads)!=1 or len(keys)!=1:raise ValueError('Unique payload and nested key descriptors required')
    fields=[f.get('name') for f in payloads[0]['fields']];cases=[f.get('name') for f in keys[0]['fields']]
    if tuple(fields)!=expected_fields or tuple(cases)!=expected_keys:raise ValueError('Pinned payload field/key contract changed')
    return payloads[0],keys[0],cases


def recover(out,control="IOSurfacePayload"):
    out=pathlib.Path(out);image=MachO(IMAGE)
    if image.u32(4)!=0x100000c:raise ValueError('Expected ARM64 image')
    metadata=inspect(IMAGE);payload,key,names=select(metadata,control)
    command=['xcrun','llvm-objdump','--macho','--arch=arm64','--disassemble','--dis-symname',CONTRACTS[control][4],IMAGE]
    result=subprocess.run(command,capture_output=True,text=True,check=True,timeout=30)
    (out/'payload-key-disassembly.txt').write_text(result.stdout)
    code=instructions(result.stdout)
    witness_address=hex(min(code));entry='indirect'
    if control=='BitmapDescription':
        body_symbol='_$s21PreviewsMessagingHost17BitmapDescriptionV3Key33_FF1D0E9CDC7C26AC16D452C8D5E8488ELLO8rawValueSSvg'
        observed=[(op,args) for op,args,_ in code.values()]
        if observed!=[('ldrb','w0, [x20]'),('b',body_symbol)]:raise ValueError('Pinned bitmap key thunk changed')
        command[command.index('--dis-symname')+1]=body_symbol
        body=subprocess.run(command,capture_output=True,text=True,check=True,timeout=30).stdout
        (out/'payload-key-body-disassembly.txt').write_text(body)
        code=instructions(body);entry='w0'
    elif control=='ServiceMessagePayload':
        if len(names)!=1:raise ValueError('Constant getter requires singleton enum')
        entry='constant'
    rows=[{'metadata_case':name,'selector_index':i,**interpret(image,code,i,entry=entry)} for i,name in enumerate(names)]
    atomic(out/'payload-keys.json',{'image_sha256':digest(IMAGE),'image_uuid':image.uuid,'control':control,'payload_descriptor':payload,
           'key_descriptor':key,'records':rows,'getter_address':hex(min(code)),'witness_address':witness_address,'entry_mode':entry,
           'scope':'Static native key witness interpretation and field descriptors. Not live wire keys, envelope selection, completion, or numeric transport IDs.'})
    return {'field_count':len(payload['fields']),'key_count':len(rows),'fields_match_keys':[f['name'] for f in payload['fields']]==names,
            'keys_match_cases':all(r['raw_value']==r['metadata_case'] for r in rows),
            'keys_match_fields':all(r['raw_value']==r['metadata_case'] for r in rows) and [f['name'] for f in payload['fields']]==names,
            'raw_values':[r['raw_value'] for r in rows],'image_sha256':digest(IMAGE),'image_uuid':image.uuid,
            'scope':'Pinned host static codec key witness only. No resource import, Swift ABI invocation or service contact.'}
