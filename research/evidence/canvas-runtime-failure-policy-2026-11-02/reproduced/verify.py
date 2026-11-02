"""Verify actual policy-release traces; logging delivery and assertion delegates stay unknown."""
from pathlib import Path
import argparse,json
MODES=['policy-debug-unfulfilled','policy-soft-unfulfilled','policy-fatal-unfulfilled','policy-debug-fulfilled','policy-soft-fulfilled','policy-fatal-fulfilled']
def verify(root):
 root=Path(root);out={}
 for mode in MODES:
  result=json.loads((root/("native-"+mode+".result.json")).read_text());rows=[json.loads(x) for x in (root/("native-"+mode+".stdout")).read_text().splitlines()];events=[r['event'] for r in rows]
  assert rows[0]['pid']==result['pid'] and not result['timeout'];assert [r['seq'] for r in rows]==list(range(1,len(rows)+1))
  assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]));configured=next(r for r in rows if r['event']=='policy-configured')
  kind=mode.split('-')[1];fulfilled=mode.endswith('-fulfilled') and not mode.endswith('-unfulfilled')
  assert configured['marker']==2 and configured['payload']=={'debug':0,'soft':1,'fatal':2}[kind] and configured['fulfilled']==fulfilled
  assert events.index('policy-configured')<events.index('policy-release-begin')
  if mode=='policy-fatal-unfulfilled':
   assert result['code']==-5 and 'policy-release-end' not in events and 'pass' not in events and 'probe-deinit' not in events
   assert 'Fatal error: concurrent invalidation handle was deallocated without being invalidated.' in (root/("native-"+mode+".stderr")).read_text()
   out[mode]='owned SIGTRAP with explicit native unfulfilled-handle diagnostic';continue
  assert result['code']==0 and rows[-1]['event']=='pass'
  callbacks=[r['name'] for r in rows if r['event']=='callback'];assert callbacks==(['policy-probe'] if fulfilled else [])
  died=[r for r in rows if r['event']=='probe-deinit'];assert len(died)==1 and died[0]['name']=='policy-probe' and died[0]['close_result']==0
  end=next(r for r in rows if r['event']=='policy-release-end');assert end['context_released'] and end['fd_closed']
  assert died[0]['seq']<end['seq'];assert events.index('policy-release-begin')<events.index('policy-release-end')<events.index('cancel-begin')
  if fulfilled:assert died[0]['seq']<next(r['seq'] for r in rows if r['event']=='policy-release-begin')
  else:assert next(r['seq'] for r in rows if r['event']=='policy-release-begin')<died[0]['seq']
  out[mode]='returned and owned context/FD cleanup observed'
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');print(json.dumps(verify(p.parse_args().directory),indent=2))
