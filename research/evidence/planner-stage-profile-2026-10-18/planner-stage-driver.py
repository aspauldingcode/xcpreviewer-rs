import sys,subprocess,json,time,pathlib
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller
p=pathlib.Path('/private/tmp/planner-stage-20261018');p.mkdir(exist_ok=False)
with Controller().lock():
 t=time.monotonic()
 with (p/'trace.stdout').open('wb') as o,(p/'trace.stderr').open('wb') as e:
  try:
   r=subprocess.run([sys.executable,'/private/tmp/planner-stage-diagnostic.py'],stdout=o,stderr=e,timeout=12)
   result={'exit_code':r.returncode,'timed_out':False}
  except subprocess.TimeoutExpired:result={'exit_code':None,'timed_out':True}
 result['seconds']=time.monotonic()-t
 (p/'outcome.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
