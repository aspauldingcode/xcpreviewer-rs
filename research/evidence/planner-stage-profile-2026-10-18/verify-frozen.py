from pathlib import Path
import json,hashlib,sys,subprocess
b=Path(__file__).resolve().parent
seal=json.loads((b/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=b/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
from profile import summarize
expected=json.loads((b/'result.json').read_text())
for name in ['artifact','full-cost']:
 actual=summarize([json.loads(s) for s in (b/(name+'.stdout')).read_text().splitlines()])
 if actual!=expected[name]:raise ValueError('summary')
 outcome=json.loads((b/(name+'-outcome.json')).read_text())
 if outcome['exit_code']!=0 or outcome['timed_out'] is not False or not 0<=outcome['seconds']<22:raise ValueError('outcome')
if expected['full-cost']['result']['execution_started'] is not False or expected['full-cost']['result']['candidates']!=[]:raise ValueError('execution')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(b/'test_profile.py')],check=True,capture_output=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'synthetic_methods':6,'native_execution':False,'full_inspection_complete':True}))
