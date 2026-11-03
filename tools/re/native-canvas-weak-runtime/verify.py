"""Verify owned weak controls and recorded class observations; no native weak claim."""
from pathlib import Path
import json,collections,hashlib

def verify(root):
 r=Path(root)
 fixture=[json.loads(x) for x in (r/'reproduction-build/controls.stdout').read_text().splitlines()];assert [x['control'] for x in fixture]==[0,1,2] and all(x['passed'] and x['owned_fd_closed'] for x in fixture)
 blocked=[json.loads(x) for x in (r/'load-blocked/events.jsonl').read_text().splitlines()];assert any('different Team IDs' in x.get('message',{}).get('description','') for x in blocked)
 assert any(x['stage']=='failure' for x in blocked) and not any(x.get('message',{}).get('payload',{}).get('event')=='hooks-ready' for x in blocked)
 ui=json.loads((r/'ui-blocked/ui-error.json').read_text());assert ui['mac_locked'] and not ui['ui_actions_executed']
 guard=[json.loads(x) for x in (r/'wrong-target/events.jsonl').read_text().splitlines()];assert guard[0]['stage']=='failure' and guard[0]['error']=='Target executable mismatch' and json.loads((r/'wrong-target/result.json').read_text())['exit_code']==1
 results={}
 for name in ['file-a','file-b']:
  p=r/name;rows=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()];assert not any(x['stage'] in ['failure','cleanup-unconfirmed','unload-error'] or x.get('message',{}).get('type')=='error' for x in rows)
  assert rows[-1]['source_restored']
  events=[x['message']['payload'] for x in rows if x['stage']=='script' and x['message'].get('type')=='send']
  ready=next(x for x in events if x['event']=='hooks-ready');assert ready['uuid']=='afaf513ac1153755840e1d82b40e7d93' and not ready['helper_module_loaded'] and not ready['weak_reference_access_available']
  observed=[x for x in events if x['event']=='editor-scene-observed'];assert observed and all(x['expected_class'] and x['main'] and not x['weak_liveness_verified'] for x in observed)
  begins={x['call_id']:x for x in events if x['event']=='method-enter'};ends={x['call_id']:x for x in events if x['event']=='method-return'};assert set(begins)==set(ends) and 0<len(begins)<=200
  assert len(begins)==sum(x['event']=='method-enter' for x in events)
  ids={x['id'] for x in observed};counts=collections.Counter()
  for ident,a in begins.items():
   b=ends[ident];assert a['method']==b['method'] and a['scene_id']==b['scene_id'] and a['thread']==b['thread'] and a['main'] and b['main'];assert events.index(a)<events.index(b);assert a['scene_id'] in ids;counts[a['method']]+=1
  assert counts['pinning-didset']>0 and counts['deinitializing']==counts['deallocating']==counts['removed-files']==0
  before=(p/'source-before.swift').read_bytes();assert hashlib.sha256(before).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  after=before+b'\n#Preview("Runtime addition", traits: .fixedLayout(width: 80, height: 40)) {\n    Color.orange.frame(width: 80, height: 40)\n}\n';assert next(x for x in rows if x['stage']=='source-added')['sha256']==hashlib.sha256(after).hexdigest()
  for label in ['file-added','file-restored']:
   snap=json.loads((p/(label+'.json')).read_text());assert not snap['weak_reference_access_available'];assert snap['identity_scope']=='address correlation only; unobserved reuse possible'
   assert snap['objects'] and all(not any(v for k,v in obj.items() if k!='id') for obj in snap['objects'])
  clean=next(x for x in events if x['event']=='cleanup-done');assert clean['listeners_detached'] and clean['weak_boxes_created']==0 and not clean['helper_module_loaded']
  results[name]={'pinning_entries_returns':counts['pinning-didset'],'first_observed_address_tokens':len(observed),'deinitializer_entries_observed':0,'weak_liveness_or_resource_release_verified':False}
 final=json.loads((r/'final-controls.json').read_text());assert final['source_restored_controller_available'] and final['xcode_left_running'] and not final['native_weak_lifetime_verified'] and not final['project_binding_verified']
 return {'owned_weak_fd_controls':3,'load_helper_route_rejected':True,'ui_actions_not_exercised_mac_locked':True,'native_class_observation':results,'artifact_check_reran_native':False}
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1]),indent=2))
