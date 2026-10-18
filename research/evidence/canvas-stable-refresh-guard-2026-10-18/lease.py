import sys,json,time,datetime,select,hashlib
from pathlib import Path
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller,atomic
from reloop.xcodebridge import BrokerClient,manage
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs');plan=json.loads((p/'experiment.json').read_text());cp=r/'research/loop/continuous.json';deadline=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00')).timestamp();source=Path(plan['workspace']).parent/'Sources/PreviewLab/PreviewLab.swift';counter=0

def checkpoint(status):
 v=json.loads(cp.read_text());v['canvas_input_stable_checkpoint']={'status':status,'working_root':str(p),'workspace':plan['workspace'],'source_sha256':plan['source_sha256'],'deadline_utc':plan['deadline_utc'],'next_action':'Reconcile exact owned workspace and zero-window/source checks before any further controller work if cleanup is unverified. No new opening or native action until reconciliation.'};atomic(cp,v)
def windows():
 global counter
 if deadline-time.time()<9:raise ValueError('backend reserve missed; cleanup reconciliation required')
 value=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}});counter+=1;(p/('windows-%d.json'%counter)).write_text(json.dumps(value,indent=2)+'\n')
 if value.get('isError') is not False and 'isError' in value:raise ValueError('MCP error')
 data=value.get('structuredContent')
 if data is None:data=json.loads(value['content'][0]['text'])
 if not isinstance(data,dict) or not isinstance(data.get('message'),str):raise ValueError('listing')
 return data['message']
with Controller().lock():
 if time.time()>=datetime.datetime.fromisoformat(plan['stop_new_actions_utc'].replace('Z','+00:00')).timestamp():raise ValueError('navigation reserve missed')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('source changed')
 if deadline-time.time()<25:raise ValueError('initial backend reserve missed')
 status=manage('status');(p/'bridge-before.json').write_text(json.dumps(status,indent=2)+'\n')
 if not status['running'] or not status['responsive']:raise ValueError('bridge lost; no restart')
 if windows()!='No workspace windows found':raise ValueError('Prior workspace cleanup absent')
 checkpoint('owned_open_possible_cleanup_unverified')
 print(json.dumps({'ready':True,'deadline':plan['deadline_utc']}),flush=True)
 cleaned=False
 try:
  while time.time()<deadline:
   ready,_,_=select.select([sys.stdin],[],[],min(1,max(0,deadline-time.time())))
   if not ready:continue
   line=sys.stdin.readline(16385)
   if not line or len(line)>16384:break
   request=json.loads(line)
   if request=={'op':'windows'}:print(json.dumps({'windows':windows()}),flush=True)
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
