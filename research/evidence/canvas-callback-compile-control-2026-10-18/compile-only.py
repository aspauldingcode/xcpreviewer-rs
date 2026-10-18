import sys,json,hashlib,datetime
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller,execute
from reloop.libprocobserver import Observer
# Separate compilation-only feasibility plan. No executable invocation or Xcode session.
DEADLINE=datetime.datetime(2026,10,18,18,24,tzinfo=datetime.timezone.utc).timestamp()
helper=r/'research/build/libproc-observer/owned-process-snapshot'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
def pins():
 for n,h in json.loads((p/'pins.json').read_text()).items():
  if sha(Path(n) if n.startswith('/') else p/n)!=h:raise ValueError('Changed pin '+n)
 if sha(helper)!='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5':raise ValueError('Observer identity')
with Controller().lock():
 pins()
 if DEADLINE-datetime.datetime.now(datetime.timezone.utc).timestamp()<125:raise ValueError('Compilation reserve missed; no renewal')
 results=[]
 for name,args in [
 ('cli-compile',['/usr/bin/xcrun','swiftc','-module-cache-path',str(p/'cli-compile/ModuleCache'),str(p/'ReceiptWriter.swift'),str(p/'main.swift'),'-o',str(p/'cli-compile/probe')]),
 ('ui-typecheck',['/usr/bin/xcrun','swiftc','-typecheck','-parse-as-library','-module-cache-path',str(p/'ui-typecheck/ModuleCache'),str(p/'ReceiptWriter.swift'),str(p/'PreviewFixture.swift')])]:
  pins()
  if DEADLINE-datetime.datetime.now(datetime.timezone.utc).timestamp()<60:raise ValueError('Phase reserve missed; no renewal')
  out=p/name;out.mkdir();events=[]
  result=execute(args,out,45,268435456,event=lambda kind,payload:events.append({'event':kind,**payload}),observer=Observer(helper).snapshot)
  record={'argv':args,'result':result,'events':events};(out/'execution.json').write_text(json.dumps(record,indent=2)+'\n');results.append(record)
  # A failed compile is a retained discriminating result; do not retry or change inputs.
 (p/'result.json').write_text(json.dumps({'phases':results,'executable_invocations':0,'ui_sessions':0,'receipt_publications':0,'deadline_closed':True},indent=2)+'\n')
 print(json.dumps({'phases':[v['result'] for v in results],'executable_invocations':0}))
