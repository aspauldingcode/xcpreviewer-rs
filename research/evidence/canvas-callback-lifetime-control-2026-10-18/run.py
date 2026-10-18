import sys,json,hashlib,datetime
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));sys.path.insert(0,str(p))
from reloop.core import Controller,execute
from reloop.libprocobserver import Observer
from decoder import expected,canonical,filename,directory
DEADLINE=datetime.datetime(2026,10,18,18,33,tzinfo=datetime.timezone.utc).timestamp()
helper=r/'research/build/libproc-observer/owned-process-snapshot';binary=Path('/private/tmp/callback-compile-20261018/cli-compile/probe')
def sha(x):return hashlib.sha256(Path(x).read_bytes()).hexdigest()
def pins():
 for n,h in json.loads((p/'pins.json').read_text()).items():
  if sha(Path(n) if n.startswith('/') else p/n)!=h:raise ValueError('Pin changed '+n)
def reserve():
 if DEADLINE-datetime.datetime.now(datetime.timezone.utc).timestamp()<25:raise ValueError('Lifetime reserve missed; no renewal')
with Controller().lock():
 pins();reserve();root=p/'receipts';root.mkdir(mode=0o700);results=[]
 for name,code in [('positive',0),('duplicate',1)]:
  pins();reserve();out=p/name;out.mkdir();receipts=root/name;receipts.mkdir(mode=0o700);events=[]
  result=execute([sys.executable,'-B',str(p/'owned-wrapper.py'),str(binary),str(receipts),name],out,4,1048576,event=lambda kind,payload:events.append({'event':kind,**payload}),observer=Observer(helper).snapshot)
  execution={'result':result,'events':events};(out/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
  if result['execution']!='success' or result['exit_code']!=0:raise ValueError('Wrapper gate')
  report=json.loads((out/'stdout.txt').read_bytes());starts=[x for x in events if x['event']=='process_started']
  if len(starts)!=1 or report['wrapper_pid']!=starts[0]['pid'] or report['timed_out'] is not False or report['child_wait']!=code:raise ValueError('Actual child wait/PID linkage')
  if not any(x['event']=='owned_descendant_cleanup' for x in events):raise ValueError('Cleanup')
  identity={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':report['child_pid'],'view':'01234567-89ab-cdef-0123-456789abcdef'}
  raw={f.name:f.read_bytes().hex() for f in receipts.iterdir()}
  if name=='positive':directory(receipts,identity,3)
  else:
   first=expected(identity,'appear',0,0);conflict=expected(identity,'increment',0,1)
   if set(raw)!={filename(first),'.pending-'+filename(conflict)}:raise ValueError('Duplicate namespace')
   if bytes.fromhex(raw[filename(first)])!=canonical(first) or bytes.fromhex(raw['.pending-'+filename(conflict)])!=canonical(conflict):raise ValueError('Duplicate full bytes')
   try:directory(receipts,identity,0)
   except ValueError:pass
   else:raise ValueError('Pending accepted')
  results.append({'name':name,'identity':identity,'files_hex':raw,'report':report,'execution':execution,'bytes_compared':sum(len(bytes.fromhex(v)) for v in raw.values())})
 (p/'result.json').write_text(json.dumps({'controls':results,'UI_input_qualified':False,'scope':'Owned CLI receipts with observed wrapper root and actual child wait. Child continuous observation not established.','deadline_closed':True},indent=2)+'\n')
 print(json.dumps({'controls':[(x['name'],x['bytes_compared']) for x in results],'UI_input_qualified':False}))
