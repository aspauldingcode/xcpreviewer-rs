from pathlib import Path
import argparse,json

def verify(root):
 root=Path(root);qualification=json.loads((root/'qualification.json').read_text());assert qualification['associated_typeref']=='SS7message_t'
 result={}
 for mode,fulfilled in [('policy-log-unfulfilled',False),('policy-log-fulfilled',True)]:
  r=json.loads((root/(mode+'.trace-result.json')).read_text());assert r['code']==0 and r['failed'] is None
  rows=[json.loads(x) for x in (root/(mode+'.stdout')).read_text().splitlines()];assert rows[0]['pid']==r['pid'];assert [x['seq'] for x in rows]==list(range(1,len(rows)+1))
  assert rows[-1]['event']=='pass';events=[x['event'] for x in rows]
  t=next(x for x in rows if x['event']=='associated-type-qualified');assert t['type']=='(message: Swift.String)' and t['size']==16
  configured=next(x for x in rows if x['event']=='policy-configured');assert configured['kind']=='log' and configured['marker']==1 and configured['fulfilled']==fulfilled
  assert events.index('policy-ready-for-hooks')<events.index('policy-release-begin')<events.index('policy-release-end')
  end=next(x for x in rows if x['event']=='policy-release-end');assert end['context_released'] and end['fd_closed']
  assert [x['name'] for x in rows if x['event']=='callback']==(['policy-probe'] if fulfilled else [])
  died=[x for x in rows if x['event']=='probe-deinit'];assert len(died)==1 and died[0]['close_result']==0 and died[0]['seq']<end['seq']
  hooks=json.loads((root/(mode+'.hooks.json')).read_text());assert not any(x['type']=='error' for x in hooks)
  payloads=[x['payload'] for x in hooks if x['type']=='send'];assert payloads[0]['event']=='hooks-ready'
  if fulfilled:assert len(payloads)==1
  else:
   assert [x['event'] for x in payloads]==['hooks-ready','native-log-enabled-result','native-log-api-enter']
   assert payloads[1]['enabled']==1 and payloads[1]['caller_offset']=='0x2bd4c'
   assert payloads[2]['caller_offset']=='0x2be2c' and payloads[2]['type']==16
  result[mode]={'returned':True,'owned_context_fd_cleaned':True,'native_logging_api_called':not fulfilled}
 for mode,fulfilled in [('policy-log-unfulfilled',False),('policy-log-fulfilled',True)]:
  r=json.loads((root/('gated-'+mode+'.result.json')).read_text());rows=[json.loads(x) for x in (root/('gated-'+mode+'.stdout')).read_text().splitlines()]
  assert r['code']==0 and not r['timeout'] and r['frida_attached'] is False and rows[0]['pid']==r['pid']
  assert rows[-1]['event']=='pass' and any(x['event']=='policy-ready-for-hooks' for x in rows)
  end=next(x for x in rows if x['event']=='policy-release-end');assert end['context_released'] and end['fd_closed']
  assert [x['name'] for x in rows if x['event']=='callback']==(['policy-probe'] if fulfilled else [])
  result['gated-'+mode]={'returned':True,'owned_context_fd_cleaned':True,'frida_attached':False}
 return result
def verify_store(root):
 root=Path(root);result={}
 for label in ['untraced','gated-untraced','traced']:
  r=json.loads((root/(label+'-store.json')).read_text());assert r.get('code')==0 and not r['timeout']
  readable=[x for x in r['selected'] if x['message']=='FulfillOnce failure: owned-policy, callsite: owned:1:1 within owned' and x['sender'].endswith('/PreviewsFoundationHost')]
  malformed=[x for x in r['selected'] if x['message']=='<compose failure [missing precomposed log]>']
  if label!='traced':assert readable, 'owned native log record not observed: '+label
  result[label]={'readable_owned_record':bool(readable),'compose_failure_record':bool(malformed),'pid':r['pid']}
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--store',action='store_true');a=p.parse_args();r={'native':verify(a.directory)};
 if a.store:r['store']=verify_store(a.directory)
 print(json.dumps(r,indent=2))
