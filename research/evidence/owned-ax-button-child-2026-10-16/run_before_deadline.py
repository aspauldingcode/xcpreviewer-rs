"""Entry gate against approval/dispatch delay; native guard retains process bounds."""
import datetime,json,os,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
phase=sys.argv[1]
if phase not in ('compile','fixture','inventory','output-valid','output-invalid','output-large','output-write'):raise ValueError('Unknown phase')
deadline=datetime.datetime(2026,10,16,19,21,52,tzinfo=datetime.timezone.utc).timestamp()
required={'compile':100,'output-valid':60,'output-invalid':100,'output-large':80,'output-write':60,'fixture':40,'inventory':20}[phase]
now=time.time()
if now+required>deadline:
 receipt={'status':'wake_budget_expired_before_dispatch','phase':phase,'observed_utc':datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-16T19:21:52+00:00','required_reserve_seconds':required,'native_launched':False}
 with (root/(phase+'-budget-rejection.json')).open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt));sys.exit(75)
os.execv(sys.executable,[sys.executable,str(root/'execute.py'),phase])
