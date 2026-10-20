from pathlib import Path
import json,sys,tempfile

def verify(r):
 for mode in ['factory-error','both-fields','deadline']:
  s=json.loads((r/(mode+'.stdout')).read_text());c=s['callback']
  assert s['mode']==mode and s['native_responder']=='BSActionResponder' and s['callbacks']==1
  assert s['callback_arrived_within_500ms'] and s['deadline_set_as_dispatch_time_uint64'] and not s['external_action_sent']
  assert c['on_configured_queue'] and (c['error_domain'],c['error_code'])==(('BSActionErrorDomain',2) if mode=='deadline' else ('Owned.SceneReply',71))
  assert c['slot1_class']==('__NSCFConstantString' if mode=='both-fields' else None)
if __name__=='__main__':
 r=Path(sys.argv[1]);verify(r);rejected=0
 with tempfile.TemporaryDirectory() as folder:
  d=Path(folder)
  for mode in ['factory-error','both-fields','deadline']:(d/(mode+'.stdout')).write_bytes((r/(mode+'.stdout')).read_bytes())
  for field,value in [('callbacks',2),('callback_arrived_within_500ms',False),('deadline_set_as_dispatch_time_uint64',False),('external_action_sent',True)]:
   p=d/'deadline.stdout';original=p.read_bytes();s=json.loads(original);s[field]=value;p.write_text(json.dumps(s))
   try:verify(d)
   except (AssertionError,ValueError):rejected+=1
   p.write_bytes(original)
  for field,value in [('on_configured_queue',False),('error_code',5)]:
   p=d/'deadline.stdout';original=p.read_bytes();s=json.loads(original);s['callback'][field]=value;p.write_text(json.dumps(s))
   try:verify(d)
   except (AssertionError,ValueError):rejected+=1
   p.write_bytes(original)
 assert rejected==6
 print(json.dumps({'native_cases':3,'native_callbacks':3,'configured_queue_callbacks':3,'receipt_mutants_rejected':6,'source_swift_callback_executed':False,'remote_target_settlement_proven':False}))
