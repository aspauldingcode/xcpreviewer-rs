"""One-task owned receive-size controls, not native Canvas or reclamation."""
import hashlib,json,re
from pathlib import Path

def need(v):
 if not v:raise ValueError('Receive-size evidence rejected')
def integer(v,n=None):return type(v) is int and (n is None or v==n)
def parsed(raw):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d);d[k]=v
  return d
 def bad(v):raise ValueError('Nonfinite JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def record(row,marker=True):
 r=row['record'];p=r['report'];need(row['error'] is None and integer(p['target_code'],0) and p['failure'] is None and p['drained'] is True and integer(p['remaining_observed'],0) and r['emergencyClosed'] is False and r['privateAbortRequested'] is False)
 raw=r['stdout'].encode();need(len(raw)<=131072 and integer(r['stdoutBytes'],len(raw)) and r['stdoutSha256']==hashlib.sha256(raw).hexdigest());
 if not marker:return raw,0
 markers=re.findall(r'^owned_tree_pid:([1-9][0-9]*)$',r['stderr'],re.M);need(len(markers)==1 and 1<int(markers[0])<=2147483647);return raw,int(markers[0])
def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f);need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) is not None and f['binary_sha256']==c['binary_sha256'])
 rows=[parsed(x) for x in raw.decode().splitlines()];need(len(rows)==2)
 expected=bytearray([0xa5]*16384)
 for y in range(9):
  for x in range(17):
   for channel in range(4):expected[y*128+x*4+channel]=255 if channel==3 else (49+x*17+y*31+channel*53)&255
 for index,row in enumerate(rows):
  need(row['large'] is bool(index) and row['endpoint_removed'] is True)
  for key in set(row)-{'large','endpoint_removed'}:need(integer(row[key]))
  need(integer(row['pid'],pid) and row['resource_name']>0 and row['received_name']==row['resource_name'])
  need(row['small_code']==(268451844 if index else 0) and row['reported_size']==(64 if index else 0) and row['transfer_size']==64 and row['header_size']==24)
  need([row[k] for k in ['queued_before','queued_after','queued_final']]==[1,1,0] and [row[k] for k in ['refs_before','refs_after','refs_received','refs_destroyed','remaining_refs']]==[1,1,2,1,0])
  need(row['resource_query_after']==row['endpoint_query_after']==15 and row['stride']==128 and row['allocation_bytes']==16384)
  for name in ['before.bin','after-small.bin','received.bin','alias-after-cleanup.bin']:
   p=root/'owned-documents'/('large' if index else 'control')/name;need(not p.is_symlink() and p.read_bytes()==expected)
 return {'owned_receive_size_controls_admitted':True,'cases':2,'full_bytes_compared':131072,'padding_bytes':4320,'unused_tail_bytes':121856,'local_name_removal_status':15,'new_native_canvas_protocol':False,'physical_reclamation_qualified':False,'cross_task_delivery_qualified':False}
if __name__=='__main__':
 p=Path(__file__).parent;v=admitted(p);(p/'admission.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
