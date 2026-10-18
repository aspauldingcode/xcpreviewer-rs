import sys,json,hashlib,datetime,os
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));sys.path.insert(0,str(p))
from reloop.core import Controller,execute
from reloop.libprocobserver import Observer
from decoder import directory,expected,canonical,filename
DEADLINE=datetime.datetime(2026,10,18,18,25,tzinfo=datetime.timezone.utc).timestamp()
helper=r/'research/build/libproc-observer/owned-process-snapshot';sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
def pins():
 for n,h in json.loads((p/'runtime-pins.json').read_text()).items():
  if sha(Path(n) if n.startswith('/') else p/n)!=h:raise ValueError('Pin changed '+n)
def reserve():
 if DEADLINE-datetime.datetime.now(datetime.timezone.utc).timestamp()<20:raise ValueError('Runtime reserve missed; no renewal')
with Controller().lock():
 pins();reserve()
 compiled=json.loads((p/'result.json').read_text())
 if any(x['result']['execution']!='success' or x['result']['exit_code']!=0 for x in compiled['phases']):raise ValueError('Compilation prerequisite')
 root=p/'native-receipts';root.mkdir(mode=0o700)
 result={'ui_sessions':0,'native_button_input':False,'controls':[]}
 for name,code in [('positive',0),('duplicate',1)]:
  pins();reserve();out=p/('runtime-'+name);out.mkdir();receipts=root/name;receipts.mkdir(mode=0o700);events=[]
  run=execute([str(p/'cli-compile/probe'),str(receipts),name],out,3,1048576,event=lambda kind,payload:events.append({'event':kind,**payload}),observer=Observer(helper).snapshot)
  record={'result':run,'events':events};(out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
  if run['exit_code']!=code or run['execution']!=('success' if code==0 else 'failed'):raise ValueError('Actual wait outcome')
  starts=[x for x in events if x['event']=='process_started']
  if len(starts)!=1 or not any(x['event']=='owned_descendant_cleanup' for x in events):raise ValueError('Lifecycle')
  identity={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':starts[0]['pid'],'view':'01234567-89ab-cdef-0123-456789abcdef'}
  files={f.name:f.read_bytes().hex() for f in receipts.iterdir()}
  if name=='positive':directory(receipts,identity,3)
  else:
   first=expected(identity,'appear',0,0);conflict=expected(identity,'increment',0,1)
   if set(files)!={filename(first),'.pending-'+filename(conflict)}:raise ValueError('Duplicate namespace')
   if bytes.fromhex(files[filename(first)])!=canonical(first) or bytes.fromhex(files['.pending-'+filename(conflict)])!=canonical(conflict):raise ValueError('Duplicate full bytes')
   try:directory(receipts,identity,0)
   except ValueError:pass
   else:raise ValueError('Failed pending admitted')
  result['controls'].append({'name':name,'identity':identity,'files_hex':files,'actual_wait':run,'bytes_compared':sum(len(bytes.fromhex(v)) for v in files.values())})
 (p/'runtime-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'controls':[(x['name'],x['bytes_compared']) for x in result['controls']],'ui_sessions':0}))
