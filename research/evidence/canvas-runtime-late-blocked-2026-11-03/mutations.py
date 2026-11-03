"""Faults in recorded evidence only; no native execution."""
import json,tempfile,shutil,argparse
from pathlib import Path
from verify import verify
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
name='native-late-while-blocked.stdout';original=[json.loads(x) for x in (a.directory/name).read_text().splitlines()]
def find(rs,event,name=None):return next(x for x in rs if x['event']==event and (name is None or x.get('name')==name))
def field(event,key,value):return lambda rs:find(rs,event).update({key:value})
def order(rs):
 x=rs.index(find(rs,'callback','parallel-late'));y=rs.index(find(rs,'cross-thread-late-add-begin'));rs[x],rs[y]=rs[y],rs[x]
 times=sorted(v['time_ns'] for v in rs)
 for i,v in enumerate(rs):v.update(seq=i+1,time_ns=times[i])
cases={'original-context-dead':field('second-invalidate-returned-original-blocked','context_alive',False),'original-fd-closed':field('late-cleaned-original-blocked','original_fd_open',False),'late-context-retained':field('late-cleaned-original-blocked','late_context_released',False),'late-token-returned':field('cross-thread-late-add-returned','has_token',True),'cleanup-fd-open':field('parallel-cleanup-complete','fd_closed',False),'deinit-fd-mismatch':lambda rs:find(rs,'probe-deinit','parallel-late').update(fd=999),'same-thread-callback':lambda rs:find(rs,'callback','parallel-late').update(thread_id=find(rs,'callback','parallel-a')['thread_id']),'callback-before-registration-call':order}
result={}
for label,mutate in cases.items():
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp)
  for src in a.directory.glob('native-*'):
   if src.suffix in ['.stdout','.json']:shutil.copy2(src,r/src.name)
  rows=json.loads(json.dumps(original));mutate(rows);(r/name).write_text(''.join(json.dumps(v)+'\n' for v in rows))
  try:verify(r)
  except AssertionError:result[label]='rejected'
  else:raise AssertionError('accepted '+label)
print(json.dumps({'scope':'synthetic recorded-evidence mutations','results':result},indent=2))
