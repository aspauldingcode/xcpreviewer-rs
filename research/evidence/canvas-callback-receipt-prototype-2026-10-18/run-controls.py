import sys,json,hashlib,datetime,os,subprocess
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));sys.path.insert(0,str(p))
from reloop.core import Controller,execute
from reloop.libprocobserver import Observer
from decoder import directory,expected,canonical,filename
DEADLINE=datetime.datetime(2026,10,18,18,8,tzinfo=datetime.timezone.utc).timestamp()
HELPER=r/'research/build/libproc-observer/owned-process-snapshot';HELPER_SHA='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def reserve(seconds):
 if DEADLINE-datetime.datetime.now(datetime.timezone.utc).timestamp()<seconds:raise ValueError('Native reserve missed; no renewal')
def pins():
 for name,h in json.loads((p/'approved-pins.json').read_text()).items():
  f=Path(name) if name.startswith('/') else p/name
  if sha(f)!=h:raise ValueError('Pin changed: '+name)
 if sha(HELPER)!=HELPER_SHA:raise ValueError('Observer changed')
def phase(name,args,timeout,expected_code):
 pins();reserve(65 if name=='compile' else 15)
 if name!='compile' and sha(p/'probe')!=json.loads((p/'binary.json').read_text())['sha256']:raise ValueError('Binary binding changed')
 out=p/name;out.mkdir();events=[]
 def event(kind,payload):events.append({'event':kind,**payload})
 result=execute([str(a) for a in args],out,timeout,268435456,event=event,observer=Observer(HELPER).snapshot)
 (out/'execution.json').write_text(json.dumps({'result':result,'events':events},indent=2)+'\n')
 if result['exit_code']!=expected_code or result['execution']!=('success' if expected_code==0 else 'failed'):raise ValueError('Unexpected actual wait outcome')
 starts=[e for e in events if e['event']=='process_started']
 if len(starts)!=1 or not any(e['event']=='owned_descendant_cleanup' for e in events):raise ValueError('Missing observed process lifecycle')
 return starts[0]['pid']
with Controller().lock():
 pins();reserve(65)
 phase('compile',['/usr/bin/xcrun','swiftc','-module-cache-path',p/'compile/ModuleCache',p/'ReceiptWriter.swift',p/'main.swift','-o',p/'probe'],45,0)
 (p/'binary.json').write_text(json.dumps({'sha256':sha(p/'probe'),'source_hashes':{n:sha(p/n) for n in ['ReceiptWriter.swift','main.swift']},'UI_fixture_compiled':False},indent=2)+'\n')
 controls=p/'receipts';controls.mkdir(mode=0o700);identity={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':0,'view':'01234567-89ab-cdef-0123-456789abcdef'}
 positive=controls/'positive';positive.mkdir(mode=0o700)
 identity['pid']=phase('positive',[p/'probe',positive,'positive'],3,0)
 records=directory(positive,identity,3)
 result={'positive_identity':dict(identity),'positive_records':records,'positive_bytes_checked':sum(f.stat().st_size for f in positive.iterdir()),'UI_fixture_compiled':False,'Canvas_input_delivered':False}
 duplicate=controls/'duplicate';duplicate.mkdir(mode=0o700)
 identity['pid']=phase('duplicate',[p/'probe',duplicate,'duplicate'],3,1)
 first=expected(identity,'appear',0,0);pending=expected(identity,'increment',0,1)
 if (duplicate/filename(first)).read_bytes()!=canonical(first) or (duplicate/('.pending-'+filename(pending))).read_bytes()!=canonical(pending):raise ValueError('Duplicate overwrite or missing failed pending bytes')
 try:directory(duplicate,identity,0)
 except ValueError:pass
 else:raise ValueError('Pending failure was admitted')
 result.update(duplicate_identity=dict(identity),duplicate_existing_bytes=canonical(first).decode(),duplicate_pending_bytes=canonical(pending).decode(),duplicate_refused=True)
 (p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'positive_bytes_checked':result['positive_bytes_checked'],'duplicate_refused':True,'Canvas_input_delivered':False}))
