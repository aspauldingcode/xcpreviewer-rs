"""Validate the observed static continuation guard; not a runtime once-only proof."""
import re
from reloop.discriminants import instructions


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
