"""Static IOSurfacePayload keys, corroborated with nominal descriptors; no Swift ABI calls."""
import pathlib
import subprocess
from reloop.core import atomic,digest
from reloop.discriminants import IMAGE,instructions,interpret
from reloop.swiftmeta import MachO,inspect

SYMBOL='_$s21PreviewsMessagingHost16IOSurfacePayloadV3Key33_9EB199A477CFC41B350A6EFBC2D206BELLO0a10FoundationC0012PropertyListF0AagHP8rawValueSSvgTW'
EXPECTED=('surfaceID','scaleFactor','width','height','selectableRegions')


def has_ancestor(context,name):
    for _ in range(8):
        context=context.get('parent')
        if not isinstance(context,dict):return False
        if context.get('name')==name:return True
    return False


def select(metadata):
    payloads=[t for t in metadata['types'] if t.get('name')=='IOSurfacePayload' and t.get('kind')==17]
    keys=[t for t in metadata['types'] if t.get('name')=='Key' and t.get('kind')==18 and has_ancestor(t,'IOSurfacePayload')]
    if len(payloads)!=1 or len(keys)!=1:raise ValueError('Unique payload and nested key descriptors required')
    fields=[f.get('name') for f in payloads[0]['fields']];cases=[f.get('name') for f in keys[0]['fields']]
    if tuple(fields)!=EXPECTED or cases!=fields:raise ValueError('Pinned payload field/key contract changed')
    return payloads[0],keys[0],cases


def recover(out):
    out=pathlib.Path(out);image=MachO(IMAGE)
    if image.u32(4)!=0x100000c:raise ValueError('Expected ARM64 image')
    metadata=inspect(IMAGE);payload,key,names=select(metadata)
    command=['xcrun','llvm-objdump','--macho','--arch=arm64','--disassemble','--dis-symname',SYMBOL,IMAGE]
    result=subprocess.run(command,capture_output=True,text=True,check=True,timeout=30)
    (out/'payload-key-disassembly.txt').write_text(result.stdout)
    code=instructions(result.stdout)
    rows=[{'metadata_case':name,'selector_index':i,**interpret(image,code,i)} for i,name in enumerate(names)]
    atomic(out/'payload-keys.json',{'image_sha256':digest(IMAGE),'image_uuid':image.uuid,'payload_descriptor':payload,
           'key_descriptor':key,'records':rows,'getter_address':hex(min(code)),
           'scope':'Static native key witness interpretation and field descriptors. Not live wire keys, envelope selection, completion, or numeric transport IDs.'})
    return {'field_count':len(names),'key_count':len(rows),'keys_match_fields':all(r['raw_value']==r['metadata_case'] for r in rows),
            'raw_values':[r['raw_value'] for r in rows],'image_sha256':digest(IMAGE),'image_uuid':image.uuid,
            'scope':'Pinned host IOSurfacePayload static codec key witness only. No resource import, Swift ABI invocation or service contact.'}
