"""Verify executed native traces; source replay is deliberately not accepted."""
import json
from pathlib import Path
MODES=['invalidate','cancel','owner-loss','drop-waiting-token','ordering','reentrant','inflight','race','cancel-next','add-during-dispatch','cancel-admitted','self-drop','self-cancel-drop','invalidate-deinit-reentry','invalidate-deinit-add']
def verify(root,negative=False):
 root=Path(root);result={}
 for mode in MODES+(['cancel-reentry'] if negative else []):
  r=json.loads((root/('native-'+mode+'.result.json')).read_text());rows=[json.loads(x) for x in (root/('native-'+mode+'.stdout')).read_text().splitlines()];assert rows
  assert all(type(x.get('thread_id')) is int and x['thread_id']>0 for x in rows)
  assert [x['seq'] for x in rows]==list(range(1,len(rows)+1));assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]));assert rows[0]['pid']==r['pid'];assert not r['timeout']
  events=[x['event'] for x in rows];callbacks=[x['name'] for x in rows if x['event']=='callback'];dead=[x['name'] for x in rows if x['event']=='probe-deinit'];assert all(x['close_result']==0 for x in rows if x['event']=='probe-deinit')
  if mode=='cancel-reentry':
   assert r['code']==-9 and 'destructor-reentry-begin' in events and 'destructor-reentry-end' not in events and 'pass' not in events
   crash=json.loads((root/'cancel-reentry-crash.json').read_text());assert crash['pid']==r['pid'];assert any('Trying to recursively lock an os_unfair_lock' in s for lines in (crash.get('asi') or {}).values() for s in lines);result[mode]='observed recursive-lock process termination';continue
  assert r['code']==0 and rows[-1]['event']=='pass' and rows[-1]['mode']==mode
  expected={'invalidate':['first','late'],'cancel':[],'owner-loss':[],'drop-waiting-token':['drop-waiting'],'ordering':['a','c'],'reentrant':['reentrant'],'inflight':['inflight'],'race':callbacks,'cancel-next':['cancel-next-a','cancel-next-b'],'add-during-dispatch':['add-late-a','nested-late','add-late-b'],'cancel-admitted':['admitted-a','admitted-b'],'self-drop':['self-drop'],'self-cancel-drop':['self-cancel-drop'],'invalidate-deinit-reentry':['invalidate-deinit-reentry'],'invalidate-deinit-add':['invalidate-deinit-add','destructor-late']}[mode];assert callbacks==expected and rows[-1]['callbacks']==expected
  if mode=='invalidate':
   assert dead==['first','late'];assert events.index('caller-probe-dropped')<events.index('invalidate-begin')<events.index('callback')<events.index('probe-deinit')<events.index('invalidate-end');assert [x['has_token'] for x in rows if x['event']=='registered']==[True,False]
  elif mode=='cancel':assert dead==['cancelled'] and events.index('cancel-begin')<events.index('probe-deinit')<events.index('cancel-end')
  elif mode=='owner-loss':assert dead==['owner-loss'] and events.index('handle-release-begin')<events.index('probe-deinit')<events.index('handle-release-end')<events.index('cancel-begin')
  elif mode=='drop-waiting-token':assert events.index('token-destroy-end')<events.index('callback') and dead==['drop-waiting']
  elif mode=='ordering':assert sorted(dead)==['a','b','c']
  elif mode=='reentrant':assert events.index('callback-reentry-begin')<events.index('callback-reentry-end') and dead==['reentrant']
  elif mode=='inflight':
   assert dead==['inflight'];assert events.index('callback-blocked')<events.index('cancel-begin')<events.index('cancel-end')<events.index('cancel-returned-callback-still-blocked')<events.index('callback-unblocked')<events.index('probe-deinit')<events.index('invalidate-end')
   retained=next(x for x in rows if x['event']=='cancel-returned-callback-still-blocked');assert retained['context_alive'] and retained['fd_open'];assert next(x for x in rows if x['event']=='callback')['thread_id']!=retained['thread_id'];cleaned=next(x for x in rows if x['event']=='inflight-cleanup-complete');assert cleaned['context_released'] and cleaned['fd_closed']
  elif mode=='race':
   rounds=[x for x in rows if x['event']=='race-round-complete'];assert [x['round'] for x in rounds]==list(range(100));assert len(callbacks)==len(set(callbacks));assert sorted(dead)==sorted('race-'+str(i) for i in range(100))
   for x in rounds:assert x['callbacks']==callbacks.count('race-'+str(x['round'])) and x['callbacks'] in [0,1] and x['fd_closed'] and x['context_released']
   assert set(callbacks)<=set(dead)
   worker_ids={x['thread_id'] for x in rows if x['event'] in ['cancel-begin','invalidate-begin']}-{rows[0]['thread_id']};assert len(worker_ids)>=2
   active={};overlap=False
   for x in rows:
    if x['event'] in ['cancel-begin','invalidate-begin']:
     overlap=overlap or any(t!=x['thread_id'] for t in active);active[x['thread_id']]=x['event']
    elif x['event'] in ['cancel-end','invalidate-end']:active.pop(x['thread_id'],None)
   assert overlap and not active
  elif mode in ['invalidate-deinit-reentry','invalidate-deinit-add']:
   assert sorted(dead)==sorted(expected)
   cleanup=next(x for x in rows if x['event']=='destructor-cleanup-complete');assert cleanup['context_released'] and cleanup['fd_closed']
   own_deinit=next(i for i,x in enumerate(rows) if x['event']=='probe-deinit' and x['name']==mode)
   assert events.index('callback')<own_deinit<events.index('destructor-cleanup-complete')
   if mode=='invalidate-deinit-reentry':
    assert events.count('invalidate-begin')==events.count('invalidate-end')==3
    ends=[i for i,x in enumerate(rows) if x['event']=='invalidate-end']
    begins=[i for i,x in enumerate(rows) if x['event']=='invalidate-begin']
    assert begins[0]<own_deinit<events.index('destructor-reentry-begin')<begins[1]<ends[0]<events.index('destructor-reentry-end')<ends[1]<events.index('destructor-cleanup-complete')<begins[2]<ends[2]
   else:
    assert events.count('invalidate-begin')==events.count('invalidate-end')==2
    late_callback=next(i for i,x in enumerate(rows) if x['event']=='callback' and x['name']=='destructor-late')
    late_dead=next(i for i,x in enumerate(rows) if x['event']=='probe-deinit' and x['name']=='destructor-late')
    returned=next(x for x in rows if x['event']=='destructor-add-returned');assert not returned['has_token']
    assert own_deinit<events.index('destructor-add-begin')<late_callback<events.index('destructor-add-returned')<late_dead<events.index('destructor-add-end')<events.index('invalidate-end')<events.index('destructor-cleanup-complete')
    assert [x['has_token'] for x in rows if x['event']=='registered']==[True,False]
    late_cleanup=next(x for x in rows if x['event']=='destructor-add-end');assert late_cleanup['context_released'] and late_cleanup['fd_closed']
  elif mode in ['self-drop','self-cancel-drop']:
   assert dead==[mode]
   retained=next(x for x in rows if x['event']=='self-token-dropped-context-live');assert retained['context_alive'] and retained['fd_open'] and retained['cancelled']==(mode=='self-cancel-drop')
   cleanup=next(x for x in rows if x['event']=='self-cleanup-complete');assert cleanup['context_released'] and cleanup['fd_closed']
   assert events.index('callback')<events.index('token-destroy-begin')<events.index('token-destroy-end')<events.index('self-token-dropped-context-live')<events.index('self-callback-returning')<events.index('probe-deinit')<events.index('invalidate-end')<events.index('self-cleanup-complete')
   assert events.count('callback')==1 and events.count('invalidate-begin')==2 and events.count('invalidate-end')==2
   if mode=='self-cancel-drop':
    assert events.count('cancel-begin')==events.count('cancel-end')==2
    assert events.index('callback')<events.index('cancel-begin')<events.index('cancel-end')<events.index('token-destroy-begin')
   else:assert 'cancel-begin' not in events
  elif mode in ['cancel-next','add-during-dispatch','cancel-admitted']:
   cleanup=next(x for x in rows if x['event']=='dispatch-cleanup-complete');assert cleanup['context_released'] and cleanup['fds_closed'];assert len(dead)==len(callbacks) and set(dead)==set(callbacks);assert all(i<events.index('invalidate-end') for i,x in enumerate(rows) if x['event']=='probe-deinit')
   def pos(name,event='callback'):return next(i for i,x in enumerate(rows) if x['event']==event and x.get('name')==name)
   if mode=='cancel-next':
    assert pos('cancel-next-a')<events.index('callback-cancel-next-begin')<events.index('cancel-begin')<events.index('cancel-end')<events.index('callback-cancel-next-end')<pos('cancel-next-b')<events.index('invalidate-end')
   elif mode=='add-during-dispatch':
    assert pos('add-late-a')<events.index('callback-add-late-begin')<pos('nested-late')<events.index('callback-add-late-returned')<pos('nested-late','probe-deinit')<events.index('callback-add-late-end')<pos('add-late-b')
    assert [x['has_token'] for x in rows if x['event']=='registered']==[True,True,False]
   else:
    retained=next(x for x in rows if x['event']=='cancel-returned-next-not-called');assert retained['context_alive'] and retained['fd_open']
    assert events.index('callback-blocked')<events.index('cancel-begin')<events.index('cancel-end')<events.index('cancel-returned-next-not-called')<events.index('callback-unblocked')<pos('admitted-b')<pos('admitted-b','probe-deinit')<events.index('invalidate-end')
    assert rows[pos('admitted-b')]['thread_id']!=retained['thread_id']
  result[mode]='native execution passed assertions'
 return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--negative',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,a.negative),indent=2))
