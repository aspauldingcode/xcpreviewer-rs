"""Verify bounded native callback/capture accounting; no remote settlement claim."""
from pathlib import Path
import json,copy
EXPECTED={'reply':(None,None),'error':('Owned.ActionError',17),'timeout':('BSActionErrorDomain',2),'invalidate':('BSActionErrorDomain',5)}
def verify(mode,s):
    assert s['mode']==mode and s['external_action_sent'] is False
    assert s['can_send_before'] and s['valid_before'] and s['callback_arrived_within_500ms']==1
    assert s['can_send_after_wait'] is False and s['valid_after_wait'] is False
    assert s['owned_handler_capture_deallocations_after_action_release']==1
    assert s['post_invalidation_observation_ms']==150
    a=s['callbacks_at_final_queue_barrier'];assert len(a)==1 and a[0]['response_class']=='BSActionResponse'
    assert (a[0]['error_domain'],a[0]['error_code'])==EXPECTED[mode]
if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);rows={m:json.loads((root/(m+'.stdout')).read_text()) for m in EXPECTED}
    for m,s in rows.items():verify(m,s)
    base=rows['timeout'];mutants=[]
    for n in [0,2]:mutants.append({**base,'owned_handler_capture_deallocations_after_action_release':n})
    mutants.extend([{**base,'callbacks_at_final_queue_barrier':[]},{**base,'callbacks_at_final_queue_barrier':base['callbacks_at_final_queue_barrier']*2},{**base,'can_send_after_wait':True},{**base,'post_invalidation_observation_ms':0}])
    q=copy.deepcopy(base);q['callbacks_at_final_queue_barrier'][0]['error_code']=5;mutants.append(q)
    rejected=0
    for s in mutants:
        try:verify('timeout',s)
        except AssertionError:rejected+=1
    assert rejected==7
    print(json.dumps({'native_cases':4,'native_callbacks':4,'owned_capture_deallocations':4,'corruption_controls_rejected':rejected,'observation_window_ms':150,'unbounded_no_later_effect_proven':False}))
