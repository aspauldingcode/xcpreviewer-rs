"""Owned native Mach-reply trace comparator; raw bodies stay local."""
from pathlib import Path
import json,base64,hashlib,copy,sys
UUID='c40fcae87a173d8287cb3da4802adef1';LIB='/usr/lib/system/libxpc.dylib';ID=536870912
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(v):
 p=v['positive'];assert p['mode']=='positive' and p['sent']==p['received']==0 and p['id']==0x58504352;assert len(p['trace'])==2
 assert p['trace'][0]['send_id']==p['trace'][1]['receive_id']==p['id']
 assert all(t['complete']==1 and t['result']==0 and t['api']==1 for t in p['trace'])
 b=v['baseline'][0];assert b['test']=='baseline' and not b['trace'] and b['callbacks']==0 and not b['callback_arrived']
 result={};bodies=[]
 for mode,size,text in [('native',308,'owned.reply'),('native-changed',340,'owned.reply.changed.control')]:
  x=v[mode][0];assert x['test']==mode and x['expected_reply']==text and x['callback_arrived'] and x['callback_on_owned_queue'] and x['callback_payload_matches'] and x['callbacks']==1
  ts=x['trace'];assert len(ts)==3 and all(t['complete']==1 and t['api']==1 and t['caller_image']==LIB and t['caller_uuid']==UUID for t in ts)
  send,small,recv=ts;assert send['result']==0 and send['send_id']==ID and send['options']==1 and send['send_bits']==18 and send['send_size']==size and send['caller_offset']==214252
  assert small['result']==0x10004004 and small['receive_size']==308 and small['receive_message_size']==size and small['caller_offset']==213276
  assert recv['result']==0 and recv['receive_id']==ID and recv['receive_bits']==18<<8 and recv['receive_message_size']==size and recv['receive_size']==size+52 and recv['caller_offset']==213276
  sent=base64.b64decode(send['send_body'],validate=True);received=base64.b64decode(recv['receive_body'],validate=True);assert sent==received and len(sent)==size-24
  bodies.append(sent);result[mode]={'message_id':ID,'send_disposition':18,'message_bytes':size,'entire_body_bytes_equal':len(sent),'body_sha256':sha(sent),'receive_initial_capacity':308,'receive_required_message_bytes':size,'receive_retry_capacity':size+52,'callback_payload_and_owned_queue_match':True,'call_sites_image_uuid':UUID}
 assert bodies[0]!=bodies[1]
 return {'native_kernel_reply_cases':result,'total_body_bytes_compared':600,'positive_hook_control':True,'no_send_finite_control':True,'cross_process_canvas_transport':False,'final_right_retirement_proven':False}
def load(f):return {m:json.loads((f/(m+'.stdout')).read_text()) for m in ['positive','native','native-changed','baseline']}
if __name__=='__main__':
 f=Path(sys.argv[1]);v=load(f);result=verify(v);rejected=0
 for kind in range(12):
  x=copy.deepcopy(v);t=x['native'][0]['trace']
  if kind<3:
   b=bytearray(base64.b64decode(t[2]['receive_body']));b[[0,len(b)//2,len(b)-1][kind]]^=1;t[2]['receive_body']=base64.b64encode(b).decode()
  elif kind==3:t[0]['send_bits']=19
  elif kind==4:t[2]['receive_id']+=1
  elif kind==5:x['native'][0]['callback_payload_matches']=False
  elif kind==6:t[0]['caller_uuid']='wrong'
  elif kind==7:x['positive']['trace']=[]
  elif kind==8:x['baseline'][0]['callbacks']=1
  elif kind==9:t[1]['receive_message_size']-=1
  elif kind==10:t[0]['result']=1
  else:x['native-changed'][0]['trace'][2]['receive_body']=t[2]['receive_body']
  try:verify(x)
  except (AssertionError,ValueError,KeyError):rejected+=1
 assert rejected==12;result['receipt_mutations_rejected']=rejected;print(json.dumps(result))
