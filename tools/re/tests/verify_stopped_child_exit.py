import json,hashlib,os
from pathlib import Path
MODES=['stopped-0','stopped-1','running-0','running-1'];PEER=bytes([0,1,2,255,10,42,99,128]);RUNTIME='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python';LAUNCHER='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 p=json.loads((e/'prediction.json').read_text());assert p=={'modes':MODES,'root_codes':[43]*4,'child_raw_statuses':[9,9,15,15],'stopped_status':4,'child_exited':[False]*4,'child_exit_codes':[-1]*4,'child_signals':[9,9,15,15],'controlled_marker_bytes':16,'native_controls':4,'outer_seconds':15,'job_milliseconds':3000,'stop_wait_seconds':1,'watcher_seconds':4,'watcher_outer_seconds':5,'private_abort':False,'child_reaped_qualified':False,'native_canvas_qualified':False}
 revised=json.loads((e/'revised-prediction.json').read_text());expected=dict(p,child_raw_statuses=[15]*4,child_signals=[15]*4);assert revised==expected
 assert json.loads((e/'scope.json').read_text())=={'native_controls':4,'producer_assertion_failures':1,'producer_assertion_passes':3,'prediction_falsified':True,'confirmed_stopped_controls':2,'nonstopped_controls':2,'controlled_marker_bytes':16,'child_reaped_qualified':False}
 allpids=[]
 for mode,code in zip(MODES,[43]*4):
  root=e/mode;x=json.loads((root/'result.json').read_text());rec=x['record'];policy='stopped' if mode.startswith('stopped') else 'running';assert x['policy']==policy;assert x['mode']==mode and x['code']==code and x['released'] is True and x['error']==('Error: Observed compiler failed: 43' if code else None)
  wait=json.loads((e/('wait-'+mode+'.json')).read_text())
  if mode=='stopped-0':assert wait['code']==1 and wait['timeout'] is False and wait['stdout']=='' and '15 !== 9' in wait['stderr'];failure=json.loads((root/'retained-failure.json').read_text());assert '15 !== 9' in failure['error'] and failure['record']==rec
  else:assert wait=={'code':0,'timeout':False,'stdout':'owned stopped child exit pass\n','stderr':''} and not (root/'retained-failure.json').exists()
  assert rec['privateAbortRequested'] is False and rec['emergencyClosed'] is False and rec['signal']=='SIGKILL' and rec['anchorCode'] is None
  for stream in ['stdout','stderr']:assert rec[stream]=='' and rec[stream+'Bytes']==0 and rec[stream+'Sha256']==hashlib.sha256(b'').hexdigest()
  report=rec['report'];assert report==json.loads((root/'underlying-complete.json').read_text());assert report['kind']=='complete' and report['drained'] is True and report['target_code']==code and report['failure'] is None and report['tracked']==2 and report['remaining_observed']==0 and report['observations']>=3 and report['scope']=='Observed full-identity ancestry and inherited group only; unseen escapes excluded'
  proxy=json.loads((root/'anchor-pid.json').read_text());ready=json.loads((root/'ready.json').read_text());assert proxy['proxy_pid']==proxy['proxy_group']==rec['pid'] and ready['parent_group']==rec['pid'] and proxy['anchor_pid']!=rec['pid'] and ready['child_ack']=='ready'
  release=json.loads((root/'release-observation.json').read_text());assert len(release)==1;child=release[0];assert child['pid']==ready['child_pid'] and child['parent']==ready['parent_pid'] and child['group']==child['pid'] and child['state']=='L' and child['identity'][2]==RUNTIME and type(child['identity'][0]) is int and child['identity'][0]>0 and type(child['identity'][1]) is int and 0<=child['identity'][1]<1000000
  observed=[row for group in x['observed'] for row in group];assert child in observed;parents=[row for row in observed if row['pid']==ready['parent_pid']];assert parents and parents[0]['parent']==proxy['anchor_pid'] and parents[0]['group']==rec['pid'] and parents[0]['identity'][2] in [RUNTIME,LAUNCHER]
  assert not (root/'child-wait.json').exists();assert not (root/'child.raw').exists() and (root/'gate').read_bytes()==b'go' and (root/'finish').read_bytes()==b'exit'
  assert json.loads((root/'exit-intent.json').read_text())=={'parent_pid':ready['parent_pid'],'code':code,'without_child_wait':True}
  reg=json.loads((root/'registered.json').read_text());assert reg['root_pid']==ready['parent_pid'] and reg['child_pid']==ready['child_pid'] and reg['note_exit']==2147483648 and reg['note_exitstatus']==67108864 and reg['birth_rechecked'] is True and reg['stopped_requested'] is (policy=='stopped') and type(reg['child_status']) is int and 1<=reg['child_status']<=6
  if policy=='stopped':assert reg['child_status']==4 and (root/'stopped-marker.raw').read_bytes()==PEER and (root/'stop').read_bytes()==b'stop'
  else:assert reg['child_status']!=4 and not (root/'stopped-marker.raw').exists() and not (root/'stop').exists()
  assert json.loads((root/'watcher-wait.json').read_text())=={'status':0,'signal':None,'stdout':'','stderr':'','error':None}
  events=json.loads((root/'kernel-exit-events.json').read_text());assert events==[{'pid':ready['parent_pid'],'filter':-5,'flags':32821,'fflags':2147483648|67108864,'data':43<<8,'exited':True,'exit_code':43},{'pid':ready['child_pid'],'filter':-5,'flags':32821,'fflags':2147483648|67108864,'data':15,'exited':False,'exit_code':-1}];assert os.WIFSIGNALED(events[1]['data']) and os.WTERMSIG(events[1]['data'])==15
  allpids.extend([ready['parent_pid'],ready['child_pid'],proxy['anchor_pid'],proxy['proxy_pid']])
 assert len(set(allpids))==16 and json.loads((e/'slots.json').read_text())=={'used':4,'limit':4}
 env=json.loads((e/'environment.json').read_text());assert env['node_sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['python_sha256']=='271143990bc83af0fb2404a255038f5faafb96df1584ed7f085e5018c0f33ffb' and env['runtime_sha256']=='057446db49d0bb2e41903364c55c7bfee7ac04d17f60c20cea044f59d0b84e00' and env['private_bridge_available'] is False
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
 watcher=json.loads((e/'watcher.json').read_text());assert rea['watcher']['sha256']==watcher['sha256'] and rea['watcher']['architecture']=='arm64';assert len(watcher['sha256'])==64
 build=json.loads((e/'build.json').read_text());assert build['code']==0 and build['stdout']==build['stderr']==''
 header=json.loads((e/'header-constants.json').read_text());assert header['EVFILT_PROC']==-5 and header['NOTE_EXIT']==2147483648 and header['NOTE_EXITSTATUS']==67108864
 stoppedheader=json.loads((e/'stopped-state-header.json').read_text());assert stoppedheader['SSTOP']==4
 return {'native_controls':4,'root_wait_codes':[43]*4,'kernel_child_raw_statuses':[15]*4,'controlled_marker_bytes':16,'confirmed_stopped_controls':2,'nonstopped_controls':2,'original_sigkill_prediction_falsified':True,'child_reaped_qualified':False}
