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
