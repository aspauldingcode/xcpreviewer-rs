import hashlib,json
from pathlib import Path
MODES=['emoji-exact','invalid-exact','unicode-over','mixed-invalid'];RUNTIME='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python';LAUNCHER='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9';PEER=bytes([0,1,2,255,10,42,99,128])
def plan(mode):
 if mode=='emoji-exact':return [(1,bytes.fromhex('f09f9880')*16384)]
 if mode=='invalid-exact':return [(2,bytes([255])*65536)]
 if mode=='unicode-over':return [(1,bytes.fromhex('f09f9880')*16384+b'x')]
 return [(1,bytes.fromhex('f09f9880')*8192),(2,bytes([255])*32768)]
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 total=0;retained=0;pids=[]
 for mode in MODES:
  root=e/mode;assert json.loads((e/('wait-'+mode+'.json')).read_text())=={'code':0,'timeout':False,'stdout':'owned native raw output pass\n','stderr':''};d=json.loads((root/'result.json').read_text());exact=mode!='unicode-over';assert d['mode']==mode and d['manualAbort'] is exact and d['error']==('Error: Observed compiler aborted' if exact else 'Error: Observed compiler output limit');rec=d['record'];assert rec['signal']=='SIGKILL' and rec['anchorCode'] is None and rec['privateAbortRequested'] is True and rec['emergencyClosed'] is False;complete=json.loads((root/'underlying-complete.json').read_text());assert rec['report']==complete and complete['kind']=='complete' and complete['drained'] is True and complete['failure']=='abort' and complete['target_code']==43 and complete['remaining_observed']==0 and complete['tracked']==2 and complete['observations']>=3 and complete['scope']=='Observed full-identity ancestry and inherited group only; unseen escapes excluded'
  sizes={1:rec['stdoutBytes'],2:rec['stderrBytes']};assert all(type(x) is int and 0<=x<=65536 for x in sizes.values()) and sum(sizes.values())<=65536
  payloads={1:b'',2:b''};payloads.update(dict(plan(mode)));kept={fd:payloads[fd][:sizes[fd]] for fd in [1,2]}
  for fd,name in [(1,'stdout'),(2,'stderr')]:assert rec[name]==kept[fd].decode('utf-8',errors='replace') and rec[name+'Sha256']==hashlib.sha256(kept[fd]).hexdigest() and len(kept[fd])==sizes[fd]
  if exact:assert sizes=={fd:len(payloads[fd]) for fd in [1,2]}
  else:assert sizes[2]==0 and sizes[1]<=65536
  if mode=='invalid-exact':assert len(rec['stderr'].encode())==196608
  retained+=sum(sizes.values())
  proxy=json.loads((root/'anchor-pid.json').read_text());assert proxy['proxy_pid']==proxy['proxy_group']==rec['pid'] and proxy['anchor_pid']!=rec['pid'];ready=json.loads((root/'ready.json').read_text());assert ready['child_ack']=='ready' and ready['parent_group']==rec['pid'];injection=json.loads((root/'injection.json').read_text());assert injection['ready']==ready and injection['mode']==mode and injection['plan']==[{'fd':fd,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for fd,data in plan(mode)];assert json.loads((root/'injection-write.json').read_text())==[{'fd':fd,'requested_bytes':len(data),'written_bytes':len(data)} for fd,data in plan(mode)];assert injection['original']['kind']=='observed' and len(injection['original']['rows'])==1
  child=injection['original']['rows'][0];assert child['pid']==ready['child_pid'] and child['parent']==ready['parent_pid'] and child['group']==child['pid'] and child['state']=='L' and child['identity'][2]==RUNTIME and type(child['identity'][0]) is int and child['identity'][0]>0 and type(child['identity'][1]) is int and 0<=child['identity'][1]<1000000
  observed=[x for group in d['observed'] for x in group];parent=[x for x in observed if x['pid']==ready['parent_pid']];assert parent and parent[0]['parent']==proxy['anchor_pid'] and parent[0]['group']==rec['pid'] and parent[0]['identity'][2] in [LAUNCHER,RUNTIME]
  assert json.loads((root/'child-wait.json').read_text())=={'pid':child['pid'],'raw_status':42<<8,'exited':True,'exit_code':42};raw=(root/'child.raw').read_bytes();assert raw==PEER;total+=len(raw);assert (root/'gate').read_bytes()==b'go';pids.extend([ready['parent_pid'],child['pid'],proxy['anchor_pid'],proxy['proxy_pid']])
 assert len(set(pids))==16 and total==32
 assert json.loads((e/'slots.json').read_text())=={'used':4,'limit':4}
 env=json.loads((e/'environment.json').read_text());assert env['node_sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['python_sha256']=='271143990bc83af0fb2404a255038f5faafb96df1584ed7f085e5018c0f33ffb' and env['runtime_sha256']=='057446db49d0bb2e41903364c55c7bfee7ac04d17f60c20cea044f59d0b84e00' and env['platform']=='ProductName:\t\tmacOS\nProductVersion:\t\t26.5.1\nBuildVersion:\t\t25F80\n' and env['private_bridge_available'] is False
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
 p=json.loads((e/'prediction.json').read_text());assert p['modes']==MODES and p['limit']==65536 and p['native_controls']==4 and p['parent_wait']==43 and p['child_wait']==42 and p['controlled_peer_bytes']==32 and p['outer_seconds']==15 and p['job_milliseconds']==3000
 return {'native_controls':4,'parent_wait_codes':[43]*4,'child_wait_codes':[42]*4,'controlled_peer_bytes':32,'retained_output_bytes':retained,'combined_limit':65536,'fixed_prefix_qualified':False}
