"""Semantic corruption of recorded native traces; no SDK execution."""
from pathlib import Path
import argparse,json,tempfile,shutil
from verify import verify,MODES
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
def event(d,n):return next(v for v in d['trace'] if v['event']==n)
def before_return(d):
 rows=d['trace'];a=rows.index(event(d,'callback-returning'));b=rows.index(event(d,'capture-deinit'));rows[a],rows[b]=rows[b],rows[a];times=sorted(v['time_ns'] for v in rows)
 for i,v in enumerate(rows):v.update(seq=i+1,time_ns=times[i])
cases={'capture-dropped-during-cancel':('cancel-inflight',lambda d:event(d,'cancel-returned-blocked').update(capture_drops=1)),'inflight-reply-invalidated':('cancel-inflight',lambda d:d.update(marker_after=False)),'fd-close-failed':('normal',lambda d:event(d,'capture-deinit').update(close_result=-1)),'deinit-before-callback-return':('normal',before_return),'pending-reply-dictionary':('cancel-pending',lambda d:d.update(dictionary_before=True)),'late-extra-callback':('cancel-pending',lambda d:d.update(callbacks=2)),'wrong-accepted-peer':('normal',lambda d:d.update(peer_pid=d['pid']+1)),'invented-client-peer-identity':('normal',lambda d:d.update(server_pid=d['pid']))}
result={}
for name,(mode,mutate) in cases.items():
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp)
  for mode_name in MODES:
   for suffix in ['.stdout','.result.json']:shutil.copy2(a.directory/(mode_name+suffix),r/(mode_name+suffix))
  records=[json.loads(x) for x in (r/(mode+'.stdout')).read_text().splitlines()];d=records[-1];mutate(d)
  # Rebuild streamed copies too: assertions must reject semantic faults, not
  # merely inconsistent duplicate representations.
  (r/(mode+'.stdout')).write_text(''.join(json.dumps(v)+'\n' for v in [*d['trace'],d]))
  try:verify(r)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
