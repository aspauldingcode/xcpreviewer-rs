import sys,json,time,datetime,select,hashlib
from pathlib import Path
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller,atomic
from reloop.xcodebridge import BrokerClient,manage
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs');plan=json.loads((p/'experiment.json').read_text());cp=r/'research/loop/continuous.json';deadline=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')).timestamp();source=Path(plan['workspace']).parent/'Sources/PreviewLab/PreviewLab.swift';counter=0;receipt_observations=0

def checkpoint(status):
 v=json.loads(cp.read_text());v['canvas_live_host_inventory_checkpoint']={'status':status,'working_root':str(p),'workspace':plan['workspace'],'source_sha256':plan['source_sha256'],'deadline_utc':plan['deadline_utc'],'next_action':'Reconcile exact owned workspace and zero-window/source checks before any further controller work if cleanup is unverified. No new opening or native action until reconciliation.'};atomic(cp,v)
def windows():
 global counter
 if deadline-time.time()<9:raise ValueError('backend reserve missed; cleanup reconciliation required')
 value=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}});counter+=1;(p/('windows-%d.json'%counter)).write_text(json.dumps(value,indent=2)+'\n')
 if value.get('isError') is not False and 'isError' in value:raise ValueError('MCP error')
 data=value.get('structuredContent')
 if data is None:data=json.loads(value['content'][0]['text'])
 if not isinstance(data,dict) or not isinstance(data.get('message'),str):raise ValueError('listing')
 return data['message']
def check_pins():
 for name,want in json.loads((p/'approved-pins.json').read_text()).items():
  path=Path(name) if name.startswith('/') else p/name
  if hashlib.sha256(path.read_bytes()).hexdigest()!=want:raise ValueError('approved pin changed: '+name)
with Controller().lock():
 check_pins()
 if time.time()>=datetime.datetime.fromisoformat(plan['stop_new_actions_utc'].replace('Z','+00:00')).timestamp():raise ValueError('navigation reserve missed')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('source changed')
 if deadline-time.time()<25:raise ValueError('initial backend reserve missed')
 status=manage('status');(p/'bridge-before.json').write_text(json.dumps(status,indent=2)+'\n')
 if not status['running'] or not status['responsive']:raise ValueError('bridge lost; no restart')
 if windows()!='No workspace windows found':raise ValueError('Prior workspace cleanup absent')
 checkpoint('owned_open_possible_cleanup_unverified')
 print(json.dumps({'ready':True,'deadline':plan['deadline_utc'],'binding':{k:plan[k] for k in ['nonce','workspace','source_sha256','stop_new_actions_utc','deadline_utc']}}),flush=True)
 cleaned=False
 try:
  while time.time()<deadline:
   ready,_,_=select.select([sys.stdin],[],[],min(1,max(0,deadline-time.time())))
   if not ready:continue
   line=sys.stdin.readline(16385)
   if not line or len(line)>16384:break
   request=json.loads(line)
   if request=={'op':'windows'}:print(json.dumps({'windows':windows()}),flush=True)
   elif request=={'op':'receipts'}:
    if receipt_observations>=1:raise ValueError('receipt observation budget exhausted')
    receipt_observations+=1
    check_pins()
    if deadline-time.time()<20:raise ValueError('receipt reserve missed')
    import os,stat
    from reloop.libprocobserver import Observer
    root=Path(plan['receipt_root']);entries=list(root.iterdir())
    if len(entries)>2:raise ValueError('receipt count exceeds reviewed observation bound')
    records=[]
    for entry in entries:
     fd=os.open(entry,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
     try:
      info=os.fstat(fd)
      if not stat.S_ISREG(info.st_mode) or info.st_size>512:raise ValueError('receipt shape')
      raw=os.read(fd,513)
     finally:os.close(fd)
     value=json.loads(raw);pid=value['pid']
     if type(pid) is not int or not 1<pid<2**31:raise ValueError('receipt PID')
     observer=Observer(r/'research/build/libproc-observer/owned-process-snapshot')
     check_pins()
     rows=observer.snapshot({pid},{})
     records.append({'name':entry.name,'raw_hex':raw.hex(),'live_identity':rows.get(pid)})
    (p/'receipt-observation.json').write_text(json.dumps({'records':records,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
    print(json.dumps({'receipt_observation':records}),flush=True)
   elif request=={'op':'finish'}:
    message=windows()
    if message!='No workspace windows found':raise ValueError('owned cleanup unverified')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('source changed after UI session')
    checkpoint('owned_cleanup_verified_review_pending');cleaned=True
    (p/'cleanup.json').write_text(json.dumps({'owned_workspace_windows':0,'broker_message':message,'source_sha256':plan['source_sha256'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
    print(json.dumps({'finished':True,'owned_workspace_windows':0}),flush=True);break
   else:raise ValueError('unsupported lease command')
 finally:
  if not cleaned:checkpoint('cleanup_unverified_blocks_further_controller_work')
