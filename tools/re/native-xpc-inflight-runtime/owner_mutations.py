"""Semantic owner-release evidence faults; no native calls."""
from pathlib import Path
import argparse,json,tempfile,shutil
from verify import verify,MODES,OWNER_MODES
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
def event(d,n):return next(v for v in d['trace'] if v['event']==n)
def reorder(d):
 rows=d['trace'];i=rows.index(event(d,'client-owner-release-returned-blocked'));j=rows.index(event(d,'callback-returning'));rows[i],rows[j]=rows[j],rows[i];times=sorted(v['time_ns'] for v in rows)
 for i,v in enumerate(rows):v.update(seq=i+1,time_ns=times[i])
cases={'capture-dead-at-release-return':('release-inflight',lambda d:event(d,'client-owner-release-returned-blocked').update(capture_drops=1)),'fd-closed-at-release-return':('release-inflight',lambda d:event(d,'client-owner-release-returned-blocked').update(capture_fd_open=False)),'release-flag-false':('release-pending',lambda d:d.update(caller_client_reference_released_while_blocked=False)),'owner-release-after-callback-marker':('release-inflight',reorder),'release-return-wrong-thread':('release-inflight',lambda d:event(d,'client-owner-release-returned-blocked').update(thread_id=event(d,'callback-blocked')['thread_id'])),'error-reply-no-longer-valid':('release-pending',lambda d:d.update(invalid_after=False)),'dictionary-no-longer-valid':('release-inflight',lambda d:d.update(marker_after=False)),'fd-cleanup-not-observed':('release-pending',lambda d:d.update(fd_closed=False))}
result={}
for name,(mode,mutate) in cases.items():
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp)
  for n in MODES+OWNER_MODES:
   for ext in ['.stdout','.result.json']:shutil.copy2(a.directory/(n+ext),r/(n+ext))
  d=json.loads((r/(mode+'.stdout')).read_text().splitlines()[-1]);mutate(d)
  (r/(mode+'.stdout')).write_text(''.join(json.dumps(v)+'\n' for v in [*d['trace'],d]))
  try:verify(r,True)
  except AssertionError:result[name]='rejected'
  else:raise AssertionError('accepted '+name)
print(json.dumps({'scope':'synthetic recorded-evidence faults','results':result},indent=2))
