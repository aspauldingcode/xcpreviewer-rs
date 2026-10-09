"""Validate the observed static continuation guard; not a runtime once-only proof."""
import re
from reloop.discriminants import instructions
from reloop.discriminants import pc_relative
import struct


def inspect(text):
    code=instructions(text)
    locks=[int(m[1],16) for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+.*symbol stub for: _os_unfair_lock_lock\s*$',text,re.M)]
    unlocks=[int(m[1],16) for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+.*symbol stub for: _os_unfair_lock_unlock\s*$',text,re.M)]
    fulfills=[p for p,(op,args,_) in code.items() if op=='bl' and 'FulfillOnceState' in args and 'fulfill' in args]
    callbacks=[p for p,(op,args,_) in code.items() if (op,args)==('blr','x19')]
    if any(len(xs)!=1 for xs in (locks,unlocks,fulfills,callbacks)):raise ValueError('Unique observed guard sites required')
    lock,unlock,fulfill,callback=locks[0],unlocks[0],fulfills[0],callbacks[0]
    if not lock<fulfill<unlock<callback:raise ValueError('Guard/callback order changed')
    for p in (lock-4,unlock-4):
        if code[p][:2]!=('add','x0, x23, #0x4c'):raise ValueError('Observed lock identity changed')
    if code[unlock+4][:2]!=('ldrb','w8, [sp]') or code[unlock+8][:2]!=('cmp','w8, #0x1'):raise ValueError('Observed outcome discriminator changed')
    branch=code[unlock+12]
    if branch[0]!='b.eq' or int(branch[1],0)!=callback+4:raise ValueError('Observed callback-skip branch changed')
    if code[callback+4][0]!='ldp':raise ValueError('Callback skip must reach reviewed epilogue')
    return {'guard_verified':True,'callback_after_unlock':True,'skipped_outcome_tag':1,
            'sites':{k:hex(v) for k,v in [('lock',lock),('fulfill',fulfill),('unlock',unlock),('callback',callback)]},
            'scope':'Pinned static guard pattern only; outcome meaning, runtime races, repeated completion and cancellation require separate evidence.'}


def inspect_default(text,image):
    code=instructions(text)
    expected={0x4820:('ldr','q0, [x9, #0x920]'),0x4824:('str','q0, [x8]'),
              0x4828:('mov','w9, #0x2'),0x482c:('strb','w9, [x8, #0x10]'),0x4830:('ret','')}
    if set(code)!=set(expected)|{0x481c}:raise ValueError('Unexpected default getter extent')
    if code[0x481c][0]!='adrp' or not code[0x481c][1].startswith('x9, '):raise ValueError('Unexpected default constant base')
    if any(code[p][:2]!=value for p,value in expected.items()):raise ValueError('Unexpected default getter dataflow')
    address=pc_relative(code[0x481c][2],0x481c,True)+0x920
    offset=image.file_offset(address)
    if image.file_offset(address+15)!=offset+15:raise ValueError('Default constant crosses unmapped extent')
    raw=image.data[offset:offset+16]
    if len(raw)!=16:raise ValueError('Truncated default constant')
    low,high=struct.unpack('<QQ',raw)
    # Predicate mapping from separately anchored fail-body instruction analysis.
    branch='logging' if (low,high)==(0,0) else 'assertion-helper' if (low,high)==(1,0) else 'fatal-call-and-trap'
    return {'default_tag':2,'default_payload_words':[low,high],'default_constant_bytes':16,
            'constant_address':hex(address),'default_static_branch':branch,
            'scope':'Pinned static getter plus reviewed policy predicates. No named enum case or native mode execution claimed.'}


def inspect_cancel(text):
    code=instructions(text)
    locks=[int(m[1],16) for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+.*symbol stub for: _os_unfair_lock_lock\s*$',text,re.M)]
    unlocks=[int(m[1],16) for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+.*symbol stub for: _os_unfair_lock_unlock\s*$',text,re.M)]
    fulfills=[p for p,(op,args,_) in code.items() if op=='bl' and 'FulfillOnceState' in args and 'fulfill' in args]
    dispatches=[p for p,(op,args,_) in code.items() if (op,args)==('br','x2')]
    if any(len(xs)!=1 for xs in (locks,unlocks,fulfills,dispatches)):raise ValueError('Unique cancellation guard sites required')
    lock,unlock,fulfill,dispatch=locks[0],unlocks[0],fulfills[0],dispatches[0]
    if not lock<fulfill<unlock<dispatch:raise ValueError('Cancellation guard order changed')
    for p in (lock-4,unlock-4):
        if code[p][:2]!=('add','x0, x22, #0x4c'):raise ValueError('Cancellation lock identity changed')
    if code[unlock+4][:2]!=('ldrb','w8, [sp, #0xf]') or code[unlock+8][:2]!=('cmp','w8, #0x1'):raise ValueError('Cancellation outcome discriminator changed')
    branch=code[unlock+12]
    if branch[0]!='b.ne':raise ValueError('Cancellation dispatch condition changed')
    target=int(branch[1],0)
    if target!=dispatch-24 or code[target-4][:2]!=('ret',''):raise ValueError('Cancellation duplicate return boundary changed')
    if code[target][:2]!=('ldp','x0, x1, [x19, #0x10]') or code[target+4][:2]!=('ldr','x2, [x1, #0x8]'):raise ValueError('Cancellation indirect action boundary changed')
    return {'cancel_guard_verified':True,'cancel_action_after_unlock':True,'cancel_skipped_outcome_tag':1,
            'cancel_sites':{'lock':hex(lock),'fulfill':hex(fulfill),'unlock':hex(unlock),'dispatch':hex(dispatch)},
            'scope':'Pinned cancellation static guard and tail dispatch only; target action, runtime ordering/races and transport remain unverified.'}


def inspect_deinit(text):
    code=instructions(text)
    expected={0x2ba54:('mov','x8, x24'),0x2ba60:('mov','x0, x24'),
              0x2ba6c:('cmp','w0, #0x1'),0x2ba70:('b.ne','0x2ba88'),
              0x2ba80:('blr','x8'),0x2ba84:('b','0x2bbf0'),0x2bc3c:('ret','')}
    if any(p not in code or code[p][:2]!=value for p,value in expected.items()):raise ValueError('Deinit case/skip boundary changed')
    sites={0x2ba5c:('SynchronousAccessProviding','peek'),0x2ba68:('_swift_getEnumCaseMultiPayload',),
           0x2bb5c:('Unfulfilled',),0x2bb84:('_swift_allocError',),0x2bbd8:('FulfillmentFailureMode','fail'),0x2bc18:('_swift_release',)}
    for p,names in sites.items():
        line=next((line for line in text.splitlines() if re.match(r'^\s*%x:'%p,line)), '')
        if p not in code or code[p][0]!='bl' or not all(name in line for name in names):raise ValueError('Deinit diagnostic/cleanup call changed')
    return {'deinit_guard_verified':True,'deinit_skipped_case':1,'deinit_policy_before_common_cleanup':True,
            'scope':'Pinned static snapshot/case branch and unfulfilled diagnostic. Case naming, native deinit execution, callback completion and resource reclamation remain separate.'}


def inspect_state_metadata(data):
    candidates=[t for t in data.get('types',[]) if t.get('name')=='State' and isinstance(t.get('parent'),dict) and t['parent'].get('name')=='FulfillOnceState']
    if len(candidates)!=1:raise ValueError('Unique fulfillment State descriptor required')
    state=candidates[0];fields=state.get('fields')
    if state.get('kind')!=18 or state.get('field_count')!=2 or not isinstance(fields,list) or len(fields)!=2:raise ValueError('Fulfillment State enum shape changed')
    names=[f.get('name') for f in fields]
    if names!=['waiting','fulfilled']:raise ValueError('Fulfillment State case names changed')
    return {'state_metadata_verified':True,'state_case_names':names,'state_descriptor':state['address'],
            'scope':'Static nominal enum cases only; field order is not by itself runtime tag/ABI mapping. Unresolved symbolic types remain preserved in raw metadata.'}


def inspect_callbacks(texts):
    """Check pinned callback and constructor boundaries, not witness relocations."""
    required={0x129770,0x129858,0x1299f4,0x129a64}
    codes={}
    for text in texts:
        code=instructions(text)
        if not code:raise ValueError('Missing callback body')
        entry=min(code)
        if entry in codes:raise ValueError('Duplicate callback body')
        codes[entry]=(code,text)
    if set(codes)!=required:raise ValueError('Exact callback/constructor entries required')
    expected={
        0x129770:{0x129788:('stp','x1, x2, [x8]'),0x12978c:('stp','x3, x4, [x8, #0x10]'),0x1297e4:('str','wzr, [x0, #0x4c]'),0x1297e8:('strb','wzr, [x0, #0x49]'),0x129844:('str','x21, [x19, #0x20]')},
        0x129858:{0x129870:('stp','x1, x2, [x8]'),0x1298c8:('str','wzr, [x0, #0x4c]'),0x1298cc:('strb','wzr, [x0, #0x49]'),0x129928:('str','x21, [x19, #0x10]')},
        0x1299f4:{0x129a04:('ldr','x21, [x20]'),0x129a08:('ldp','x22, x19, [x20, #0x10]'),0x129a0c:('cbz','x21, 0x129a4c'),0x129a10:('ldr','x20, [x20, #0x8]'),0x129a44:('mov','x20, x21'),0x129a4c:('mov','x20, x19'),0x129a50:('blr','x22'),0x129a60:('ret','')},
        0x129a64:{0x129a70:('ldp','x8, x20, [x20]'),0x129a74:('blr','x8'),0x129a80:('ret','')},
    }
    for entry,checks in expected.items():
        code,text=codes[entry]
        # Repeated instruction addresses must not silently overwrite evidence.
        addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
        if len(addresses)!=len(set(addresses)):raise ValueError('Duplicate instruction address')
        if any(p not in code or code[p][:2]!=value for p,value in checks.items()):raise ValueError('Callback dataflow boundary changed')
    isolated=codes[0x1299f4][0]
    if isolated.get(0x129a48,('',))[0]!='bl' or 'verifyIsolated' not in isolated[0x129a48][1]:raise ValueError('Isolation verification call changed')
    concurrent=codes[0x129a64][0]
    if len(concurrent)!=8 or any(op=='bl' for op,args,raw in concurrent.values()):raise ValueError('Concurrent callback wrapper extent changed')
    return {'callback_boundaries_verified':True,'callback_wrapper_count':2,'isolated_optional_actor_check':True,
            'concurrent_stored_closure_dispatch':True,
            'scope':'Pinned static constructor and invoke boundaries. Witness-table relocation, concrete caller closure, actor verification behavior, scheduling, runtime completion and transport remain separate.'}


def inspect_isolation(text):
    code=instructions(text)
    addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
    if len(addresses)!=len(set(addresses)) or set(code)!=set(range(0x114e38,0x114e6c,4)):raise ValueError('Isolation helper extent changed')
    if code[0x114e5c][:2]!=('bl','0x12feb4') or 'preconditionIsolated' not in text.split('114e5c:',1)[-1].splitlines()[0]:raise ValueError('Isolation precondition call changed')
    if code[0x114e68][:2]!=('ret','') or code[0x114e58][:2]!=('mov','x1, sp'):raise ValueError('Isolation call/return boundary changed')
    if [p for p,(op,args,raw) in code.items() if op.startswith('b') or op in ('cbz','cbnz','tbz','tbnz')]!=[0x114e5c]:raise ValueError('Unexpected isolation control transfer')
    return {'isolation_precondition_verified':True,
            'scope':'Pinned helper directly calls Swift preconditionIsolated and returns normally if callee returns. Callee behavior, runtime actor identity, traps and scheduling remain unexecuted.'}


def inspect_invalidation(texts):
    """Check selected weak-owner and state-gated update boundaries."""
    codes={}
    for text in texts:
        code=instructions(text);entry=min(code)
        addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
        if entry in codes or len(addresses)!=len(set(addresses)):raise ValueError('Duplicate invalidation evidence')
        codes[entry]=code
    if set(codes)!={0x419cc,0x41f10,0x41f2c,0xbeef0}:raise ValueError('Exact invalidation boundaries required')
    shared=codes[0x41f2c];update=codes[0xbeef0]
    expected={0x41f74:('cbz','x0, 0x41fc4'),0x41f88:('add','x0, x23, #0x54'),0x41fa4:('blr','x20'),0x41fa8:('add','x0, x23, #0x54'),0x41fb0:('mov','x0, x22'),0x41fc0:('blr','x19')}
    if any(shared.get(p,())[:2]!=value for p,value in expected.items()):raise ValueError('Weak owner/lock/update/cleanup boundary changed')
    for p,target in [(0x41f70,'0x13166c'),(0x41f8c,'0x131120'),(0x41fac,'0x13112c'),(0x41fb4,'0x131498')]:
        if shared.get(p,())[:2]!=('bl',target):raise ValueError('Invalidation ownership/lock callee changed')
    checks={0xbef20:('ldrh','w8, [x0, #0x40]'),0xbef3c:('ubfx','w8, w8, #8, #8'),0xbef40:('cmp','w8, #0x1'),0xbefd0:('blr','x23'),0xbefe8:('strb','wzr, [x27, #0x41]'),0xbefec:('strb','w8, [x22, #0x8]')}
    if any(update.get(p,())[:2]!=value for p,value in checks.items()):raise ValueError('Waiting update discriminator/dataflow changed')
    for p,op,target in [(0xbef44,'b.ne','0xbef68'),(0xbef64,'b','0xbefec')]:
        if p not in update or update[p][0]!=op or update[p][1].split()[0]!=target:raise ValueError('State callback-skip branch changed')
    for p,value in [(0xbef60,1),(0xbefd4,0)]:
        if update.get(p,())[:2]!=('mov',f'w8, #0x{value:x}'):raise ValueError('Waiting update outcome changed')
    # Decode the actual B immediate at each wrapper to verify the shared handoff.
    for entry,site in [(0x419cc,0x419e4),(0x41f10,0x41f28)]:
        code=codes[entry]
        if site not in code or code[site][0]!='b':raise ValueError('Missing invalidation shared handoff')
        word=code[site][2]
        if word>>26!=5:raise ValueError('Unexpected encoded handoff')
        displacement=word&0x3ffffff
        if displacement&0x2000000:displacement-=0x4000000
        if site+displacement*4!=0x41f2c:raise ValueError('Wrong invalidation shared target')
    return {'invalidation_boundaries_verified':True,'weak_owner_absent_skips_update':True,
            'update_between_lock_unlock':True,'cleanup_after_unlock':True,'state_byte_offset':65,'skipped_state_tag':1,
            'scope':'Pinned weak-owner gate and byte1 update skip only. Dictionary effects, named runtime tags, concrete transport cancellation, executor ordering and resource reclamation remain separate.'}
