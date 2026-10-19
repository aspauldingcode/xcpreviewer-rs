from pathlib import Path
import sys,subprocess,json,hashlib,time,datetime
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 deadline=datetime.datetime(2026,10,19,9,15,tzinfo=datetime.timezone.utc).timestamp()
 if time.time()+30>deadline:raise ValueError('Fixed wake deadline expired; do not renew')
 if (p/'started.json').exists() or (p/'execution.json').exists():raise ValueError('Single execution already recorded')
 for name,h in json.loads((p/'approved-pins.json').read_text()).items():
  if hashlib.sha256((p/name).read_bytes()).hexdigest()!=h:raise ValueError('Approved source drift')
 # Recheck after lock and pin validation immediately before the owned subprocess.
 if time.time()+30>deadline:raise ValueError('Fixed wake deadline expired after admission')
 with (p/'started.json').open('x') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T09:15:00Z','executions':1},f)
 try:q=subprocess.run([sys.executable,'-B',str(p/'probe.py')],capture_output=True,text=True,timeout=20)
 except subprocess.TimeoutExpired as error:
  def plain(v):return v.decode() if isinstance(v,bytes) else v or ''
  (p/'execution.json').write_text(json.dumps({'exit':None,'timeout':True,'stdout':plain(error.stdout),'stderr':plain(error.stderr),'executions':1,'retry':False,'native_UI_execution':False},indent=2)+'\n');raise
 (p/'execution.json').write_text(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T09:15:00Z','executions':1,'native_UI_execution':False},indent=2)+'\n');print(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr}))
 if q.returncode:raise SystemExit(q.returncode)
