from pathlib import Path
import json,hashlib,base64,subprocess,sys
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
for name,h in seal['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError(name)
for name,h in json.loads((p/'approved-pins.json').read_text()).items():
 if not name.startswith('/') and hashlib.sha256((p/name).read_bytes()).hexdigest()!=h:raise ValueError('local approved pin changed')
dispatch=json.loads((p/'dispatch.json').read_text())
if type(dispatch['native_jobs_started']) is not int or dispatch['native_jobs_started']!=0 or dispatch['actual_driver_exit_code']!=1 or dispatch['UI_fixture_compiled'] is not False or dispatch['no_retry_or_deadline_extension'] is not True:raise ValueError('dispatch scope')
for name in dispatch['absence_checked']:
 if (p/name).exists():raise ValueError('Unexpected native artifacts')
from decoder import expected,canonical,filename,record
campaign=json.loads((p/'model-cases.json').read_text());identity=campaign['identity'];name=filename(expected(identity,'appear',0,0));admitted=0
if len(campaign['cases'])!=19 or campaign['tier']!='synthetic only':raise ValueError('campaign scope')
for row in campaign['cases']:
 raw=base64.b64decode(row['raw_base64'],validate=True)
 if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('model bytes')
 try:record(raw,name,identity,'appear',0,0);result=True
 except ValueError:result=False
 if result is not row['expected_admission']:raise ValueError('model admission')
 admitted+=result
if admitted!=1:raise ValueError('positive count')
for opt in [[],['-O']]:subprocess.run([sys.executable,*opt,'-B',str(p/'test_decoder.py')],capture_output=True,check=True,timeout=10)
print(json.dumps({'verified':True,'files':len(seal['files']),'synthetic_methods':7,'synthetic_cases':19,'rejected_cases':18,'native_jobs':0,'Swift_compilation_verified':False,'Canvas_input_qualified':False}))
