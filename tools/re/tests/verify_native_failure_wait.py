import json,hashlib
from pathlib import Path
MODES=['failure-0','failure-1','success-0','success-1'];PEER=bytes([0,1,2,255,10,42,99,128]);RUNTIME='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python';LAUNCHER='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 p=json.loads((e/'prediction.json').read_text());assert p=={'modes':MODES,'root_codes':[43,43,0,0],'child_code':42,'peer_bytes':list(PEER),'native_controls':4,'outer_seconds':15,'job_milliseconds':3000,'private_abort':False,'native_canvas_qualified':False}
 allpids=[]
 for mode,code in zip(MODES,[43,43,0,0]):
  root=e/mode;x=json.loads((root/'result.json').read_text());rec=x['record'];assert x['mode']==mode and x['code']==code and x['released'] is True and x['error']==('Error: Observed compiler failed: 43' if code else None)
  assert json.loads((e/('wait-'+mode+'.json')).read_text())=={'code':0,'timeout':False,'stdout':'owned native failure wait pass\n','stderr':''}
  assert rec['privateAbortRequested'] is False and rec['emergencyClosed'] is False and rec['signal']=='SIGKILL' and rec['anchorCode'] is None
  for stream in ['stdout','stderr']:assert rec[stream]=='' and rec[stream+'Bytes']==0 and rec[stream+'Sha256']==hashlib.sha256(b'').hexdigest()
  report=rec['report'];assert report==json.loads((root/'underlying-complete.json').read_text());assert report['kind']=='complete' and report['drained'] is True and report['target_code']==code and report['failure'] is None and report['tracked']==2 and report['remaining_observed']==0 and report['observations']>=3 and report['scope']=='Observed full-identity ancestry and inherited group only; unseen escapes excluded'
  proxy=json.loads((root/'anchor-pid.json').read_text());ready=json.loads((root/'ready.json').read_text());assert proxy['proxy_pid']==proxy['proxy_group']==rec['pid'] and ready['parent_group']==rec['pid'] and proxy['anchor_pid']!=rec['pid'] and ready['child_ack']=='ready'
  release=json.loads((root/'release-observation.json').read_text());assert len(release)==1;child=release[0];assert child['pid']==ready['child_pid'] and child['parent']==ready['parent_pid'] and child['group']==child['pid'] and child['state']=='L' and child['identity'][2]==RUNTIME and type(child['identity'][0]) is int and child['identity'][0]>0 and type(child['identity'][1]) is int and 0<=child['identity'][1]<1000000
  observed=[row for group in x['observed'] for row in group];assert child in observed;parents=[row for row in observed if row['pid']==ready['parent_pid']];assert parents and parents[0]['parent']==proxy['anchor_pid'] and parents[0]['group']==rec['pid'] and parents[0]['identity'][2] in [RUNTIME,LAUNCHER]
  assert json.loads((root/'child-wait.json').read_text())=={'pid':ready['child_pid'],'raw_status':42<<8,'exited':True,'exit_code':42};assert (root/'child.raw').read_bytes()==PEER and (root/'gate').read_bytes()==b'go' and (root/'finish').read_bytes()==b'exit'
  assert json.loads((root/'exit-intent.json').read_text())=={'parent_pid':ready['parent_pid'],'code':code,'after_child_wait':True}
  allpids.extend([ready['parent_pid'],ready['child_pid'],proxy['anchor_pid'],proxy['proxy_pid']])
 assert len(set(allpids))==16 and json.loads((e/'slots.json').read_text())=={'used':4,'limit':4}
 env=json.loads((e/'environment.json').read_text());assert env['node_sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['python_sha256']=='271143990bc83af0fb2404a255038f5faafb96df1584ed7f085e5018c0f33ffb' and env['runtime_sha256']=='057446db49d0bb2e41903364c55c7bfee7ac04d17f60c20cea044f59d0b84e00' and env['private_bridge_available'] is False
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
 return {'native_controls':4,'root_wait_codes':[43,43,0,0],'child_wait_codes':[42]*4,'controlled_peer_bytes':32,'private_abort_requests':0,'failure_accepted_as_success':False}
