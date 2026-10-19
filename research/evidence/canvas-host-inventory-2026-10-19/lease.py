import sys,json,time,datetime,select,hashlib,subprocess
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller,atomic
from reloop.xcodebridge import manage,BrokerClient
plan=json.loads((p/'experiment.json').read_text());deadline=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')).timestamp();source=Path('/private/tmp/callback-ui-access-20261018/workspace/Sources/PreviewLab/PreviewLab.swift');source_sha='469d33d81d8dce43070f88b69ef30b6fbcedf530dca61145338c12e5eda62b24';cp=r/'research/loop/continuous.json'
def pins():
 for n,h in json.loads((p/'approved-pins.json').read_text()).items():
  f=Path(n) if n.startswith('/') else p/n
  if hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('pin changed '+n)
def windows():
 if deadline-time.time()<10:raise ValueError('backend reserve')
 result=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}})
 data=result.get('structuredContent') or json.loads(result['content'][0]['text'])
 if result.get('isError',False) or data.get('message')!='No workspace windows found':raise ValueError('zero windows unverified')
 return result
with Controller().lock():
 pins()
 if deadline-time.time()<40:raise ValueError('initial reserve')
 status=manage('status')
 if not status['running'] or not status['responsive']:raise ValueError('Bridge unavailable; no restart')
 (p/'bridge-before.json').write_text(json.dumps(status,indent=2)+'\n');(p/'windows-before.json').write_text(json.dumps(windows(),indent=2)+'\n')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:raise ValueError('source changed')
 # Existing pinned public helper only; zero signals, UI or process launches beyond this helper.
 helper=r/'research/build/libproc-observer/owned-process-snapshot';expected=plan['expected']
 x=subprocess.run([str(helper),str(expected['pid'])],capture_output=True,timeout=2)
 if len(x.stdout)>1048576:raise ValueError('snapshot output bound')
 record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':x.returncode,'stderr':x.stderr.decode(errors='replace'),'expected':expected,'process':None,'unrelated_descendant_rows_retained':False}
 if x.returncode:raise ValueError(record)
 rows=json.loads(x.stdout);matches=[row for row in rows if row.get('pid')==expected['pid']]
 if len(matches)>1:raise ValueError('duplicate PID')
 if matches:
  row=matches[0]
  if row.get('identity')!=expected['identity']:record['process']={'pid':expected['pid'],'identity':[0,0,'/identity-mismatch-redacted'],'state':row.get('state')};record['identity_mismatch']=True
  else:record['process']=row
 (p/'process-observation.json').write_text(json.dumps(record,indent=2)+'\n')
 v=json.loads(cp.read_text());v['canvas_host_inventory_checkpoint']={'status':'passive_inventory_pending','working_root':str(p),'deadline_utc':plan['deadline_utc'],'no_workspace_opened':True};atomic(cp,v)
 print(json.dumps({'ready':True,'process':record['process'],'deadline':plan['deadline_utc']}),flush=True)
 done=False
 try:
  while time.time()<deadline:
   ready,_,_=select.select([sys.stdin],[],[],min(1,max(0,deadline-time.time())))
   if not ready:continue
   line=sys.stdin.readline(1024)
   if not line:break
   if json.loads(line)!={'op':'finish'}:raise ValueError('unsupported request')
   pins();w=windows()
   if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:raise ValueError('source changed')
   (p/'closure.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owned_workspace_windows':0,'source_sha256':source_sha,'windows':w,'workspace_opens':0,'app_selections':0},indent=2)+'\n')
   v=json.loads(cp.read_text());v['canvas_host_inventory_checkpoint']['status']='passive_inventory_closed_review_pending';atomic(cp,v);done=True;print(json.dumps({'finished':True,'owned_workspace_windows':0}),flush=True);break
 finally:
  if not done:
   v=json.loads(cp.read_text());v['canvas_host_inventory_checkpoint']['status']='passive_inventory_failed_no_workspace_opened';atomic(cp,v)
