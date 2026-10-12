import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 compile=json.loads((e/'compile.json').read_text());assert compile['code']==0 and compile['timeout'] is False
 wait=json.loads((e/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stderr']=='';rows=[json.loads(x) for x in wait['stdout'].splitlines()];assert len(rows)==2
 expected=bytearray([165])*16384
 for y in range(9):
  for x in range(17):
   for c in range(4):expected[y*128+x*4+c]=255 if c==3 else (49+x*17+y*31+c*53)&255
 total=0;parents=[];children=[]
 for row,phase,code,exit_,signal,cleanup in zip(rows,['after-import','before-ack'],[0,268451843],[42,-1],[0,9],['explicit','process-teardown']):
  for k,v in {'phase':phase,'width':17,'height':9,'seed':49,'stride':128,'allocation_bytes':16384,'mach_error':code,'peer_exit':exit_,'peer_signal':signal,'receiver_cleanup':cleanup,'local_resource_refs_retained':1,'completion_accepted':False,'late_ack_received':False,'audit_peer_verified':True,'failure_observed':True,'local_resource_name_removed':True,'peer_endpoint_name_removed':True,'rendezvous_removed':True}.items():assert row[k]==v and type(row[k]) is type(v)
  parents.append(row['sender_pid']);children.append(row['receiver_pid']);assert row['sender_pid']>1 and row['receiver_pid']>1 and row['sender_pid']!=row['receiver_pid']
  for name in ['imported.bin','retained.bin']:
   raw=(e/phase/name).read_bytes();assert raw==expected;total+=len(raw)
 assert parents[0]==parents[1] and children[0]!=children[1] and total==65536
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256']=='5e6ec2b74e80c0f1e8684c3c5c8fddf1745cae9f92512b5bb58962ecdf1bab62';assert rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 prior=json.loads((e/'prior-verification.json').read_text());assert len(prior)==3 and all(x['valid'] is True and x['external_anchor_matches'] is True for x in prior)
 return {'full_allocation_bytes':total,'padding_bytes':2160,'unused_tail_bytes':60928,'physical_reclamation':False}
