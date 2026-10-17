"""Owned queued handoff after sender-local release; no reclamation inference."""
import json,re
from pathlib import Path
from record_admit import parsed,record,integer,need

def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f)
 need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256'])
 rows=[parsed(s) for s in raw.decode().splitlines()];need(len(rows)==6)
 expected=bytearray([0xa5]*16384)
 for y in range(9):
  for x in range(17):
   for ch in range(4):expected[y*128+x*4+ch]=255 if ch==3 else (49+x*17+y*31+ch*53)&255
 changed=bytearray(expected);changed[0]^=0x5a;peers=[]
 parent_bools={'initial_move','sender_cf_released_before_go','sender_resource_handle_cleared','audit_ready_verified','audit_completion_verified','rendezvous_removed'}
 child_bools={'imported','audit_go_verified','audit_resource_verified','alias_released'}
 for index,row in enumerate(rows):
  mode=index%3;move=index>=3;need(all(integer(row[k]) for k in set(row)-parent_bools))
  need(row['sender_pid']==pid and row['receiver_pid']>1 and row['receiver_pid']!=pid and row['mode']==mode and row['surface_id']>0 and row['receiver_exit']==0)
  need(row['initial_move'] is move and row['initial_disposition']==(17 if move else 19) and row['initial_query']==(15 if move else 0) and row['resource_query_before_go']==15)
  need(all(row[k] is True for k in parent_bools-{'initial_move'}))
  need(row['remote_type_after_exit']==row['control_type_after_exit']==1048576 and row['remote_query_after_release']==row['control_query_after_release']==15)
  folder=root/'owned-documents'/(('move-' if move else 'copy-')+['control','large','small'][mode]);child=parsed((folder/'receiver.json').read_text());need(all(integer(child[k]) for k in set(child)-child_bools))
  need(child['receiver_pid']==row['receiver_pid'] and child['parent_pid']==pid and child['mode']==mode and child['small_code']==(0 if mode==0 else 268451844) and child['full_code']==(268451843 if mode==2 else 0))
  need([child[k] for k in ['queued_before','queued_after_small','queued_final']]==[1,0 if mode==2 else 1,0])
  need(child['surface_id']==(0 if mode==2 else row['surface_id']) and child['received_name']>=0 and (child['received_name']>0)==(mode!=2))
  need(child['resource_query']==(0 if mode==2 else 15) and child['inbox_query']==child['control_query']==15 and child['imported'] is (mode!=2) and child['audit_resource_verified'] is (mode!=2) and child['audit_go_verified'] is True and child['alias_released'] is True)
  names=['sender-before.bin']+(['receiver-first.bin','receiver-after-right-release.bin','receiver-mutated.bin'] if mode!=2 else [])
  need({p.name for p in folder.iterdir()}==set(names+['receiver.json']))
  for name in names:
   p=folder/name;need(p.is_file() and not p.is_symlink() and p.read_bytes()==(changed if name=='receiver-mutated.bin' else expected))
  peers.append(row['receiver_pid'])
 need(len(set(peers))==6)
 return {'queued_sender_release_admitted':True,'cases':6,'importing_cases':4,'discard_cases':2,'full_allocations':18,'full_bytes_compared':294912,'padding_bytes':9720,'unused_tail_bytes':274176,'sender_local_refs_released_before_authorization':True,'new_native_canvas_protocol':False,'physical_reclamation_qualified':False,'all_global_references_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
