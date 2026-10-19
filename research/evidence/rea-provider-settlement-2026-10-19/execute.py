from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from phase_prerequisites import parsed,require as need
H=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
with Controller().lock():
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H(p/n)==h,'approved pin')
 plan=parsed((p/'plan.json').read_text());rea=parsed((p/'rea-identity.json').read_text())
 need(H(plan['library_path'])==plan['library_sha256']==rea['sha256'] and rea['closed'] is True and rea['format']=='javascript','shipped artifact identity')
 need(H(plan['node_path'])==plan['node_sha256'],'runtime identity')
 need(time.time()+60<datetime.datetime(2026,10,19,17,30,tzinfo=datetime.timezone.utc).timestamp(),'fixed deadline reserve')
 with (p/'started.json').open('x') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T17:30:00Z'},f)
 q=subprocess.run([plan['node_path'],str(p/'run_guard.cjs')],capture_output=True,text=True,timeout=20)
 (p/'execution-outer.json').write_text(json.dumps({'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T17:30:00Z','executions':1},indent=2)+'\n')
 print(q.stdout+q.stderr)
 if q.returncode:raise SystemExit(q.returncode)
