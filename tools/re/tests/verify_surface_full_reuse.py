import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 compile=json.loads((e/'compile.json').read_text());assert compile['code']==0 and compile['timeout'] is False
 wait=json.loads((e/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stderr']=='';rows=[json.loads(x) for x in wait['stdout'].splitlines()];assert len(rows)==2
 def expected(seed):
  raw=bytearray([seed])*16384;raw[:1152]=bytes([165])*1152
  for y in range(9):
   for x in range(17):
    for c in range(4):raw[y*128+x*4+c]=255 if c==3 else (seed+x*17+y*31+c*53)&255
  return raw
 first,second=expected(49),expected(50);total=0
 for row,mode in zip(rows,['reuse','separate']):
  same=mode=='reuse';root=e/mode;peer=json.loads((root/'receiver.json').read_text())
  for k,v in {'mode':mode,'width':17,'height':9,'seed':49,'next_seed':50,'stride':128,'allocation_bytes':16384,'receiver_exit':0,'audit_peer_verified':True,'delayed_read_after_second_import':True,'rendezvous_removed':True,'sender_rights_released':True,'sender_aliases_released':True,'lookup_delay_us':100000,'settled_global_first':0,'settled_global_second':0}.items():assert row[k]==v and type(row[k]) is type(v)
  assert row['sender_pid']>1 and row['receiver_pid']>1 and row['sender_pid']!=row['receiver_pid'] and peer['receiver_pid']==row['receiver_pid']
  for key in ['first_id','second_id']:assert row[key]>0 and peer[key]==row[key]
  assert (row['first_id']==row['second_id']) is same and peer['port_names_equal'] is same
  for k,v in {'audit_peer_verified':True,'received_rights_released':True,'fixture_generations':[1,2],'first_refs_after_two_imports':2 if same else 1,'second_refs_after_first_release':1,'first_lookup_after_release':row['first_id'] if same else 0,'remaining_lookup':row['second_id'],'retired_first_lookup':0,'retired_second_lookup':0}.items():assert peer[k]==v and type(peer[k]) is type(v)
  for key,idkey in [('live_global_first','first_id'),('live_global_second','second_id')]:assert row[key]==row[idkey]
  for key,idkey in [('final_global_first','first_id'),('final_global_second','second_id')]:assert row[key] in (0,row[idkey])
  delayed=second if same else first
  for name,raw in zip(['producer-first','producer-next','delayed-first','second','after-right-release'],[first,second,delayed,second,delayed]):
   observed=(root/(name+'.bin')).read_bytes();assert observed==raw;total+=len(observed)
 assert rows[0]['sender_pid']==rows[1]['sender_pid'] and rows[0]['receiver_pid']!=rows[1]['receiver_pid'] and rows[0]['first_id']==rows[1]['first_id'] and rows[0]['final_global_first']==rows[0]['settled_global_first']==0
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256']=='6b9e4f8391af6be57b38b8f5f1b519a82b0493e35cac49a22f2e0c6223437beb' and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 assert total==163840
 return {'full_allocation_bytes':total,'padding_bytes':5400,'unused_tail_bytes':152320,'observed_cross_lifetime_id_recurrence':True,'physical_reclamation':False}
