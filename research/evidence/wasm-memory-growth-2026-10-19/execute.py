from pathlib import Path
import sys,subprocess,json,hashlib,time,datetime
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from phase_prerequisites import parsed,require as need
with Controller().lock():
 need(not (p/'started.json').exists(),'Execution already owned; no repeat')
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'Approved source drift')
 before=parsed((p/'runtime-before.json').read_text());rea=parsed((p/'rea-identity.json').read_text())
 need(hashlib.sha256(Path(before['path']).read_bytes()).hexdigest()==before['sha256']==rea['sha256'] and rea['path']==before['path'] and rea['closed'] is True and rea['architecture']=='arm64','Runtime identity')
 need(time.time()+20<datetime.datetime(2026,10,19,17,0,tzinfo=datetime.timezone.utc).timestamp(),'Fixed deadline expired')
 with (p/'started.json').open('x') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T17:00:00Z'},f)
 try:q=subprocess.run([before['path'],str(p/'probe.mjs')],capture_output=True,text=True,timeout=10)
 except subprocess.TimeoutExpired as error:
  def plain(v):return v.decode() if isinstance(v,bytes) else v or ''
  (p/'execution.json').write_text(json.dumps({'exit':None,'timeout':True,'stdout':plain(error.stdout),'stderr':plain(error.stderr),'retry':False},indent=2)+'\n');raise
 (p/'execution.json').write_text(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'timeout':False,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T17:00:00Z','executions':1},indent=2)+'\n')
 print(json.dumps({'exit':q.returncode,'fixture_executions':1,'retry':False}))
 if q.returncode:raise SystemExit(q.returncode)
