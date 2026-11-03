"""Check retained native owner/PC traces, not object/resource release."""
from pathlib import Path
import json,collections,hashlib

def verify(root):
 r=Path(root);result={}
 q=json.loads((r/'boundary-qualification.json').read_text());assert q['state_location_kind']=='interior-continuation' and q['enclosing_function_entry']=='0x23d68' and q['interior_offset']=='0x23ef0' and not q['interior_lr_is_callsite_evidence']
 assert q['owner_symbol']=='_$s10PreviewsUI18DisplayableContentV7PreviewV06CanvasD0Owxx' and q['image_sha256']=='26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab'
 for run,control in [('sampled-rpc','rpc'),('sampled-post-ack','post-ack')]:
  p=r/run;rows=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
  assert not any(x['stage'] in ['failed','unload-error'] or x.get('message',{}).get('type')=='error' for x in rows)
  assert rows[-1]['stage']=='session-ended-no-target-termination' and rows[-1]['source_restored']
  es=[x['message']['payload'] for x in rows if x['stage']=='script' and x.get('message',{}).get('type')=='send']
  ready=[x for x in es if x['event']=='hooks-ready'];assert len(ready)==1;ready=ready[0]
  assert ready['ui_uuid']=='0d87b0e2f4453035a9b6b1cf8230e015' and ready['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93'
  assert ready['function_entry']=='0x23d68' and ready['interior_points']=={'state-continuation':'0x23ef0'} and not ready['interior_return_or_caller_probe'] and not ready['tail_probe'] and ready['sampled_owner_limit_per_phase']==20
  assert not any(x['event'] in ['orphan-interior-point','owner-stack-mismatch','overflow'] for x in es)
  starts={x['id']:(i,x) for i,x in enumerate(es) if x['event']=='owner-enter'};ends={x['id']:(i,x) for i,x in enumerate(es) if x['event']=='owner-return'}
  assert starts and set(starts)==set(ends)
  assert len(starts)==sum(x['event']=='owner-enter' for x in es) and len(ends)==sum(x['event']=='owner-return' for x in es)
  phases=collections.Counter();chains=collections.Counter();points=[(i,x) for i,x in enumerate(es) if x['event']=='point'];assert all(x['owner_id'] in starts for _,x in points)
  for ident,(start,x) in starts.items():
   end,y=ends[ident];assert start<end and x['thread']==y['thread'] and x['phase']==y['phase'];phases[x['phase']]+=1
   own=[(i,z) for i,z in points if z['owner_id']==ident];assert len(own)<=1
   if own:
    i,z=own[0];assert start<i<end and z['thread']==x['thread'] and z['phase']==x['phase'] and z['point']=='state-continuation';assert 'caller_offset' not in z and 'return_address' not in z;chains[x['phase']]+=1
  assert all(v<=20 for v in phases.values()) and chains['edit']>0 and chains['restore']>0
  src=(p/'source-before.swift').read_bytes();assert hashlib.sha256(src).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
  expected_after=src+b'\n#Preview("Runtime addition", traits: .fixedLayout(width: 80, height: 40)) {\n    Color.orange.frame(width: 80, height: 40)\n}\n'
  assert next(x for x in rows if x['stage']=='source-declaration-added')['sha256']==hashlib.sha256(expected_after).hexdigest()
  stages=[x['stage'] for x in rows if x['stage']!='script'];assert stages==['capture-ready','source-edit-begin','source-declaration-added','source-declaration-removed','session-ended-no-target-termination']
  assert [x['phase'] for x in es if x['event']=='phase']==['edit','restore']
  if control=='post-ack':assert 'script.post' in (p/'session.py').read_text() and 'exports_sync.phase' not in (p/'session.py').read_text()
  result[run]={'sampled_owner_intervals':dict(phases),'owner_pc_return_chains':dict(chains),'function_entry':'0x23d68','interior_pc':'0x23ef0','separate_state_function_verified':False,'native_object_or_resource_release_verified':False}
 o=json.loads((r/'final-controls.json').read_text());assert o['source_restored_controller_available'] and o['xcode_left_running'] and not o['native_object_release_verified']
 return result
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1]),indent=2))
