from pathlib import Path
import json,argparse
MODES=['action-unfulfilled-main','action-fulfilled-main','action-unfulfilled-worker','action-fulfilled-worker']
def verify(root):
 root=Path(root);result={}
 for mode in MODES:
  receipt=json.loads((root/('native-'+mode+'.result.json')).read_text());rows=[json.loads(x) for x in (root/('native-'+mode+'.stdout')).read_text().splitlines()]
  assert receipt['code']==0 and not receipt['timeout'] and rows[0]['pid']==receipt['pid']
  assert [x['seq'] for x in rows]==list(range(1,len(rows)+1));assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]));assert rows[-1]['event']=='pass'
  def one(event,name=None):
   found=[x for x in rows if x['event']==event and (name is None or x.get('name')==name)];assert len(found)==1,(event,len(found));return found[0]
  t=one('action-associated-type');assert t['type']=='(action: @Sendable () -> ())' and t['size']==16
  held=one('action-caller-references-dropped');assert held['action_context_alive'] and held['observer_context_alive']
  begin=one('action-owner-release-begin');end=one('action-owner-release-end');clean=one('action-cleanup-complete')
  assert held['seq']<begin['seq']<end['seq']<clean['seq']
  assert clean['action_context_released'] and clean['observer_context_released'] and clean['fds_closed']
  action_dead=one('probe-deinit','action-context');observer_dead=one('probe-deinit','observer-context');assert action_dead['close_result']==observer_dead['close_result']==0
  assert begin['seq']<action_dead['seq']<end['seq'] and action_dead['thread_id']==begin['thread_id']
  worker=mode.endswith('-worker');fulfilled='-fulfilled-' in mode
  assert (begin['thread_id']!=rows[0]['thread_id'])==worker and end['thread_id']==begin['thread_id']
  actions=[x for x in rows if x['event']=='failure-action'];callbacks=[x for x in rows if x['event']=='callback']
  if fulfilled:
   assert not actions and [x['name'] for x in callbacks]==['observer-context']
   after=one('action-after-fulfillment');assert after['action_context_alive'] and after['observer_context_released']
   assert observer_dead['seq']<after['seq']<begin['seq']
  else:
   assert not callbacks and len(actions)==1
   action=actions[0];assert begin['seq']<action['seq']<action_dead['seq']<end['seq'] and action['seq']<observer_dead['seq']<end['seq']
   assert action['thread_id']==begin['thread_id'] and action['action_fd_open'] and action['observer_fd_open']
  assert one('cancel-begin')['seq']>end['seq']
  result[mode]={'failure_action_calls':len(actions),'observer_calls':len(callbacks),'action_context_retained_until_owner_release':True,'worker_release':worker,'owned_cleanup_verified':True}
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');print(json.dumps(verify(p.parse_args().directory),indent=2))
