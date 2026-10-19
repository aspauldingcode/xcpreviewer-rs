"""Owned queued handoff after sender-local release; no reclamation inference."""
import json,re,hashlib
from phase_prerequisites import receipt
from pathlib import Path
from record_admit import parsed,record,integer,need

def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f)
 receipt(root,'compile',hashlib.sha256((root/'probe.c').read_bytes()).hexdigest(),c['binary_sha256']);receipt(root,'output-valid',hashlib.sha256((root/'probe.c').read_bytes()).hexdigest(),c['binary_sha256'])
 need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256'])
 rows=[parsed(s) for s in raw.decode().splitlines()];need(len(rows)==4)
 expected=bytearray([0xa5]*16384)
 for y in range(9):
  for x in range(17):
   for ch in range(4):expected[y*128+x*4+ch]=255 if ch==3 else (49+x*17+y*31+ch*53)&255
 changed=bytearray(expected);changed[0]^=0x5a;peers=[]
 parent_bools={'initial_move','sender_cf_released_before_go','sender_resource_handle_cleared','audit_ready_verified','audit_completion_verified','rendezvous_removed'}
 child_bools={'imported','alias_acquired','alias_release_observed','cancel_before_import','audit_go_verified','audit_resource_verified'}
 for index,row in enumerate(rows):
  mode=index%2;move=index>=2;need(all(integer(row[k]) for k in set(row)-parent_bools))
  need(row['sender_pid']==pid and row['receiver_pid']>1 and row['receiver_pid']!=pid and row['mode']==mode and row['surface_id']>0 and row['receiver_exit']==0)
  need(row['initial_move'] is move and row['initial_disposition']==(17 if move else 19) and row['initial_query']==(15 if move else 0) and row['resource_query_before_go']==15)
  need(all(row[k] is True for k in parent_bools-{'initial_move'}))
  need(row['remote_type_after_exit']==row['control_type_after_exit']==1048576 and row['remote_query_after_release']==row['control_query_after_release']==15)
  folder=root/'owned-documents'/(('move-' if move else 'copy-')+['import','cancel'][mode]);child=parsed((folder/'receiver.json').read_text());need(all(integer(child[k]) for k in set(child)-child_bools))
  need(child['receiver_pid']==row['receiver_pid'] and child['parent_pid']==pid and child['mode']==mode and child['full_code']==0)
  need([child[k] for k in ['queued_before','queued_before_full','queued_final']]==[1,1,0])
  need(child['surface_id']==row['surface_id'] and child['received_name']>0 and child['resource_refs_before_destroy']==1)
  need(child['resource_query']==child['inbox_query']==child['control_query']==15)
  need(child['imported'] is (mode==0) and child['alias_acquired'] is (mode==0) and child['alias_release_observed'] is (mode==0) and child['cancel_before_import'] is (mode==1) and child['audit_resource_verified'] is True and child['audit_go_verified'] is True)
  names=['sender-before.bin']+(['receiver-first.bin','receiver-after-right-release.bin','receiver-mutated.bin'] if mode==0 else [])
  need({q.name for q in folder.iterdir()}==set(names+['receiver.json']))
  for name in names:
   q=folder/name;need(q.is_file() and not q.is_symlink() and q.read_bytes()==(changed if name=='receiver-mutated.bin' else expected))
  peers.append(row['receiver_pid'])
 need(len(set(peers))==4)
 return {'preimport_cancel_admitted':True,'cases':4,'import_cases':2,'cancel_cases':2,'full_allocations':10,'full_bytes_compared':163840,'padding_bytes':5400,'unused_tail_bytes':152320,'new_native_canvas_protocol':False,'physical_reclamation_qualified':False,'all_global_references_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
