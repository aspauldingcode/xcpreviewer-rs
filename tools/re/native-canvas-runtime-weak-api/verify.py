"""Recorded-native evidence assertions, not a native execution or simulator."""
from pathlib import Path
import argparse,json
RUNTIME='7669d858d33236c79c6c4564ffbea8d2'
def verify(r):
 rows=[json.loads(x) for x in (r/'events.jsonl').read_text().splitlines()]
 assert rows and all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
 assert not any(x['stage'] in ['failure','cleanup-unconfirmed','unload-error','restore-skipped-concurrent-edit'] for x in rows)
 script=[(i,x['message']['payload']) for i,x in enumerate(rows) if x['stage']=='script' and x['message']['type']=='send']
 assert not any(x['stage']=='script' and x['message']['type']=='error' for x in rows)
 def events(n):return [(i,v) for i,v in script if v['event']==n]
 ready=events('hooks-ready');assert len(ready)==1
 q=ready[0][1];assert q['runtime_uuid']==RUNTIME and q['uuid']=='afaf513ac1153755840e1d82b40e7d93'
 assert q['slot_size']==8 and q['helper_module_loaded'] is False and q['weak_reference_access_available'] is True and q['weak_poll_main_queue'] is True
 controls=[json.loads(x) for x in (r/'control.stdout').read_text().splitlines()]
 assert controls[0]['uuid']==RUNTIME and controls[0]['main_queue_export_matches'] is True
 assert [v['mode'] for v in controls[1:]]==[0,1,2] and all(v['passed'] and v['fd_closed'] for v in controls[1:])
 observed=events('editor-scene-observed');assert len(observed)==1
 oi,o=observed[0];assert o['expected_class'] is True and o['main'] is True and o['weak_alive_at_load'] is True
 assert not any(events(n) for n in ['class-guard-failed','capture-skipped-not-main','main-queue-guard-failed','weak-zero-or-reuse-unqualified','deinitializing-enter','deinitializing-return','deallocating-enter','deallocating-return'])
 snapshots={v['label']:(i,v) for i,v in events('snapshot')};assert len(snapshots)==3
 bi,b=snapshots['baseline'];ai,a=snapshots['file-added'];ri,s=snapshots['file-restored']
 assert b['objects']==[] and all(v['main'] is True for v in [b,a,s])
 for v in [a,s]:
  assert len(v['objects'])==1;obj=v['objects'][0]
  assert obj['id']==o['id'] and obj['weak_alive_at_load'] is True
  assert obj['deinitializing_return_seen'] is False and obj['deallocating_return_seen'] is False
 add=[i for i,v in enumerate(rows) if v['stage']=='source-added'];restore=[i for i,v in enumerate(rows) if v['stage']=='source-restored']
 assert len(add)==len(restore)==1 and bi<add[0]<oi<ai<restore[0]<ri
 enters=events('method-enter');returns=events('method-return');assert len(enters)>0 and len(enters)==len(returns)
 assert len({v['call_id'] for _,v in enters})==len(enters)
 for ei,e in enters:
  matches=[(i,v) for i,v in returns if v['call_id']==e['call_id']];assert len(matches)==1
  ti,t=matches[0];assert ei<ti and t['thread']==e['thread'] and t['scene_id']==e['scene_id']==o['id']
 cleanup=events('cleanup-done');assert len(cleanup)==1
 ci,c=cleanup[0];assert ci>ri and c['weak_slots_destroyed']==1 and c['main'] is True and c['helper_module_loaded'] is False
 assert rows[-1]['stage']=='session-ended-no-target-termination' and rows[-1]['source_restored'] is True
 return {'paired_setter_calls':len(enters),'tracked_class_receivers':1,'positive_weak_snapshots':2,'probe_weak_slots_destroyed':1,'native_deinitializer_observed':False,'native_resource_release_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();print(json.dumps(verify(a.run)))
