"""Verify executed native traces; source replay is deliberately not accepted."""
import json
from pathlib import Path
MODES=['invalidate','cancel','owner-loss','drop-waiting-token','ordering','reentrant']
def verify(root,negative=False):
 root=Path(root);result={}
 for mode in MODES+(['cancel-reentry'] if negative else []):
  r=json.loads((root/('native-'+mode+'.result.json')).read_text());rows=[json.loads(x) for x in (root/('native-'+mode+'.stdout')).read_text().splitlines()];assert rows
  assert [x['seq'] for x in rows]==list(range(1,len(rows)+1));assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]));assert rows[0]['pid']==r['pid'];assert not r['timeout']
  events=[x['event'] for x in rows];callbacks=[x['name'] for x in rows if x['event']=='callback'];dead=[x['name'] for x in rows if x['event']=='probe-deinit'];assert all(x['close_result']==0 for x in rows if x['event']=='probe-deinit')
  if mode=='cancel-reentry':
   assert r['code']==-9 and 'destructor-reentry-begin' in events and 'destructor-reentry-end' not in events and 'pass' not in events
   crash=json.loads((root/'cancel-reentry-crash.json').read_text());assert crash['pid']==r['pid'];assert any('Trying to recursively lock an os_unfair_lock' in s for lines in (crash.get('asi') or {}).values() for s in lines);result[mode]='observed recursive-lock process termination';continue
  assert r['code']==0 and rows[-1]['event']=='pass' and rows[-1]['mode']==mode
  expected={'invalidate':['first','late'],'cancel':[],'owner-loss':[],'drop-waiting-token':['drop-waiting'],'ordering':['a','c'],'reentrant':['reentrant']}[mode];assert callbacks==expected and rows[-1]['callbacks']==expected
  if mode=='invalidate':
   assert dead==['first','late'];assert events.index('caller-probe-dropped')<events.index('invalidate-begin')<events.index('callback')<events.index('probe-deinit')<events.index('invalidate-end');assert [x['has_token'] for x in rows if x['event']=='registered']==[True,False]
  elif mode=='cancel':assert dead==['cancelled'] and events.index('cancel-begin')<events.index('probe-deinit')<events.index('cancel-end')
  elif mode=='owner-loss':assert dead==['owner-loss'] and events.index('handle-release-begin')<events.index('probe-deinit')<events.index('handle-release-end')<events.index('cancel-begin')
  elif mode=='drop-waiting-token':assert events.index('token-destroy-end')<events.index('callback') and dead==['drop-waiting']
  elif mode=='ordering':assert sorted(dead)==['a','b','c']
  elif mode=='reentrant':assert events.index('callback-reentry-begin')<events.index('callback-reentry-end') and dead==['reentrant']
  result[mode]='native execution passed assertions'
 return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--negative',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,a.negative),indent=2))
