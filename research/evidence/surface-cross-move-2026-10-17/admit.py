"""Cross-task error recovery evidence, independently expected full allocations."""
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
 for index,row in enumerate(rows):
  mode=index%3;move=index>=3
  need(all(integer(row[k]) for k in ['sender_pid','receiver_pid','mode','surface_id','receiver_exit','sender_refs_before','sender_refs_after_error','sender_refs_after_retry','sender_refs_after_exit','sender_removed_query','initial_query','initial_query_after_error','initial_disposition']))
  need(row['sender_pid']==pid and row['mode']==mode and row['receiver_pid']>1 and row['receiver_pid']!=pid and row['surface_id']>0 and row['receiver_exit']==0 and row['sender_removed_query']==15)
  need(all(row[k]==1 for k in ['sender_refs_before','sender_refs_after_retry','sender_refs_after_exit']))
  need(integer(row['sender_refs_after_error'],0 if move else 1) and row['initial_move'] is move and row['reacquired_resource'] is move and row['initial_query']==row['initial_query_after_error']==(15 if move else 0) and row['initial_disposition']==(17 if move else 19))
  need(all(row[k] is True for k in ['rendezvous_removed','audit_ready_verified','audit_stage1_verified','audit_stage3_verified']))
  folder=root/'owned-documents'/(('move-' if move else 'copy-')+['control','large','small'][mode]);child=parsed((folder/'receiver.json').read_text())
  need(all(integer(child[k]) for k in set(child)-{'audit_retry_verified','audit_first_verified'}))
  need(child['receiver_pid']==row['receiver_pid'] and child['parent_pid']==pid and child['mode']==mode)
  need(child['small_code']==(0 if mode==0 else 268451844) and child['full_code']==(268451843 if mode==2 else 0))
  need([child[k] for k in ['queued_before','queued_after_small','queued_final']]==[1,0 if mode==2 else 1,0])
  need(child['retry_id']==row['surface_id'] and child['first_id']==(0 if mode==2 else row['surface_id']))
  need(child['retry_name']>0 and child['first_name']>=0 and (child['first_name']>0)==(mode!=2))
  need(child['first_query']==(0 if mode==2 else 15) and child['retry_query']==15 and child['endpoint_query']==15 and child['imported_right_refs']==1 and child['audit_retry_verified'] is True and child['audit_first_verified'] is (mode!=2))
  names=['sender-before.bin','sender-after-error.bin','sender-mutated.bin','sender-after-exit.bin','receiver-retry.bin','receiver-after-right-release.bin']+(['receiver-first.bin'] if mode!=2 else [])
  need({p.name for p in folder.iterdir()}==set(names+['receiver.json']))
  for name in names:
   p=folder/name;need(p.is_file() and not p.is_symlink() and p.read_bytes()==(expected if name in ['sender-before.bin','sender-after-error.bin','receiver-first.bin'] else changed))
  peers.append(row['receiver_pid'])
 need(len(set(peers))==6)
 return {'cross_task_move_reacquisition_admitted':True,'cases':6,'full_allocations':40,'full_bytes_compared':655360,'padding_bytes':21600,'unused_tail_bytes':609280,'copy_sender_error_refs':1,'move_sender_error_name_query':15,'new_native_canvas_protocol':False,'physical_reclamation_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
