import hashlib,json
from pathlib import Path
ERROR='Error: Owned synchronous observation callback failure'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 for mode in ['protocol','0','1']:
  wait=json.loads((e/('wait-'+mode+'.json')).read_text());assert wait=={'code':0,'timeout':False,'stdout':('protocol controls pass' if mode=='protocol' else 'native control pass')+'\n','stderr':''}
 roots=[('protocol-before',False),('protocol-after',False),('native-0',True),('native-1',True)];pids=[]
 for name,native in roots:
  row=json.loads((e/name/'result.json').read_text());after=row['phase']=='after';assert row['kind']==('native' if native else 'protocol') and row['callbacks']==1 and row['error']==ERROR and row['originalPreserved'] is True and row['lateAbsent'] is True and not (e/name/'late').exists();record=row['record'];assert record['signal']=='SIGKILL' and record['anchorCode'] is None and record['privateAbortRequested'] is True and record['emergencyClosed'] is False and record['stdout']==record['stderr']==''
  if not after:assert record['report'] is None and row['observed']==[[]];continue
  report=record['report'];assert report['kind']=='complete' and report['drained'] is True and report['failure']=='abort' and report['target_code']==-15 and report['remaining_observed']==0
  if native:
   assert report['tracked']==1 and report['observations']>=3 and report['scope']=='Observed full-identity ancestry and inherited group only; unseen escapes excluded';assert len(row['observed'])==1 and len(row['observed'][0])==1;target=row['observed'][0][0];assert target['state']=='L' and target['parent']==target['group']==record['pid'] and target['pid']!=record['pid'];ident=target['identity'];assert len(ident)==3 and type(ident[0]) is int and ident[0]>0 and type(ident[1]) is int and 0<=ident[1]<1000000 and ident[2]=='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9';pids.append(target['pid'])
  else:assert report['tracked']==0 and report['observations']==1 and report['scope']=='Owned protocol fixture; no target launched' and row['observed']==[[]]
 assert len(set(pids))==2
 assert json.loads((e/'scope.json').read_text())=={'protocol_controls':2,'native_controls':2,'native_canvas_qualified':False,'sampled_target_drain_qualified':True,'unseen_escapes_qualified':False,'synchronous_callback_only':True,'producer_slots_used':3,'producer_slots_limit':4}
 env=json.loads((e/'environment.json').read_text());assert env['node_sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['python_sha256']=='271143990bc83af0fb2404a255038f5faafb96df1584ed7f085e5018c0f33ffb' and env['platform']=='ProductName:\t\tmacOS\nProductVersion:\t\t26.5.1\nBuildVersion:\t\t25F80\n' and env['private_bridge_available'] is False
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
 pred=json.loads((e/'prediction.json').read_text());assert pred['before_callback_kills_without_complete'] is True and pred['after_callback_requests_abort_and_waits_complete'] is True and pred['native_target_wait_expected']==-15 and pred['native_runs']==2 and pred['producer_slots']==4 and pred['node_seconds']==15 and pred['job_seconds']==3
 return {'protocol_controls':2,'native_controls':2,'target_wait_codes':[-15,-15],'callback_error_preserved':True,'sampled_drained':True,'unseen_escapes_qualified':False}
