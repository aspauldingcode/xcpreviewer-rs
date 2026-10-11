"""Connect runtime observations to static identities, disassembly and decompilation."""
import pathlib
from reloop.core import atomic, digest, load
from reloop.engine import analyze, dispatch
from reloop.swiftmeta import MachO
from reloop.trace import smoke


def connected(out):
    out=pathlib.Path(out)
    observations=smoke('frida_smoke',out)
    target=out/'owned-trace-target'
    analysis=analyze(target,'preview_probe_tick',out/'analysis')
    prepared=analysis['prepared']
    if len(prepared)!=1:raise RuntimeError('Expected one exact owned tick export')
    address=prepared[0]['address'];program=analysis['program']
    static_address=int(address,16)
    base=int(analysis['program_info']['image_base'],16)
    module=MachO(target)
    links=[]
    events=load(out/'frida-events.json')
    for event in events:
        if event.get('kind')!='tick':continue
        offset=int(event['offset'],16)
        if base+offset!=static_address:raise RuntimeError('ASLR normalization does not match known export')
        if event['image'].get('uuid')!=module.uuid:raise RuntimeError('Runtime/static Mach-O UUID mismatch')
        links.append({'image_sha256':digest(target),'image_uuid':module.uuid,'offset':hex(offset),
                      'ghidra_address':address,'symbol':prepared[0]['symbol'],'event_sequence':event['sequence'],
                      'input':event['input'],'output':event['output']})
    for operation in ['decompile_function','disassemble_function','get_xrefs_to','get_xrefs_from']:
        dispatch(operation,{'program':program,'address':address},out/'analysis')
    code=load(out/'analysis/decompile_function.json')['result']
    if not str(code).strip():raise RuntimeError('Empty decompilation')
    atomic(out/'joined-trace.json',{'scope':'Owned synthetic helper; binary hash + UUID + unslid function offset, not timing-only correlation.',
                                  'links':links,'program':program,'static_address':address})
    return {**observations,'linked_events':len(links),'uuid_match':True,'address_match':True,
            'decompile_nonempty':True,'scope':'Connected owned runtime/static fixture, not canvas IPC recovery'}
