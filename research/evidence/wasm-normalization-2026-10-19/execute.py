from pathlib import Path
import sys,subprocess,json,hashlib,time,datetime
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 if (p/'started.json').exists():raise ValueError('Execution already owned; no repeat')
 for n,h in json.loads((p/'approved-pins.json').read_text()).items():
  if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h:raise ValueError('Approved source drift')
 if time.time()+20>datetime.datetime(2026,10,19,9,35,tzinfo=datetime.timezone.utc).timestamp():raise ValueError('Fixed deadline expired')
 with (p/'started.json').open('x') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T09:35:00Z'},f)
 try:q=subprocess.run(['node',str(p/'probe.mjs')],capture_output=True,text=True,timeout=10)
 except subprocess.TimeoutExpired as error:
  def plain(v):return v.decode() if isinstance(v,bytes) else v or ''
  (p/'execution.json').write_text(json.dumps({'exit':None,'timeout':True,'stdout':plain(error.stdout),'stderr':plain(error.stderr),'retry':False},indent=2)+'\n');raise
 (p/'execution.json').write_text(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T09:35:00Z','executions':1},indent=2)+'\n');print(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr}))
 if q.returncode:raise SystemExit(q.returncode)
