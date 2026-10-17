import hashlib,json,tempfile,unittest
from pathlib import Path
from admit import admitted

def encode(r,rows):
 raw=''.join(json.dumps(x)+'\n' for x in rows);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
def build(p):
 r={'error':None,'binary_sha256':'a'*64,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stderr':'owned_tree_pid:123\n'}};rows=[]
 base=bytearray([0xa5]*16384)
 for y in range(9):
  for x in range(17):
   for ch in range(4):base[y*128+x*4+ch]=255 if ch==3 else (49+x*17+y*31+ch*53)&255
 changed=bytearray(base);changed[0]^=0x5a
 for index in range(6):
  mode=index%3;move=index>=3;row=dict(sender_pid=123,receiver_pid=124+index,mode=mode,surface_id=50+index,receiver_exit=0,initial_move=move,initial_disposition=17 if move else 19,initial_query=15 if move else 0,resource_query_before_go=15,sender_cf_released_before_go=True,sender_resource_handle_cleared=True,remote_type_after_exit=1048576,control_type_after_exit=1048576,remote_query_after_release=15,control_query_after_release=15,audit_ready_verified=True,audit_completion_verified=True,rendezvous_removed=True);rows.append(row)
  folder=p/'owned-documents'/(('move-' if move else 'copy-')+['control','large','small'][mode]);folder.mkdir(parents=True)
  child=dict(receiver_pid=124+index,parent_pid=123,mode=mode,small_code=0 if mode==0 else 268451844,full_code=268451843 if mode==2 else 0,queued_before=1,queued_after_small=0 if mode==2 else 1,queued_final=0,surface_id=0 if mode==2 else 50+index,received_name=0 if mode==2 else 901,resource_query=0 if mode==2 else 15,inbox_query=15,control_query=15,imported=mode!=2,audit_go_verified=True,audit_resource_verified=mode!=2,alias_released=True)
  (folder/'receiver.json').write_text(json.dumps(child))
  for name in ['sender-before.bin']+(['receiver-first.bin','receiver-after-right-release.bin','receiver-mutated.bin'] if mode!=2 else []):(folder/name).write_bytes(changed if name=='receiver-mutated.bin' else base)
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class AdmissionTests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);build(p);self.assertEqual(admitted(p)['full_bytes_compared'],294912)
 def test_faults(self):
  faults=['wait','drain','remaining','abort','binary','hash','bytes','sender_pid','peer_pid','peer_exit','cf_retained','handle_retained','query_before_go','disposition','initial_query','remote_type','control_type','remote_cleanup','control_cleanup','audit_ready','audit_complete','rendezvous','child_pid','mode','small_code','full_code','queue','false_id','false_name','false_query','audit_go','false_import','false_audit','alias_retained','endpoint','pixel','padding','tail','stale_mutation','extra_file','missing_file','duplicate','typed']
  for fault in faults:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);r,rows=build(p);row=rows[5];folder=p/'owned-documents/move-small';cpath=folder/'receiver.json';child=json.loads(cpath.read_text())
    if fault=='wait':r['record']['report']['target_code']=7
    elif fault=='drain':r['record']['report']['drained']=False
    elif fault=='remaining':r['record']['report']['remaining_observed']=1
    elif fault=='abort':r['record']['privateAbortRequested']=True
    elif fault=='binary':r['binary_sha256']='b'*64
    elif fault=='hash':r['record']['stdoutSha256']='0'*64
    elif fault=='bytes':r['record']['stdoutBytes']+=1
    elif fault=='sender_pid':row['sender_pid']=999
    elif fault=='peer_pid':row['receiver_pid']=123
    elif fault=='peer_exit':row['receiver_exit']=23
    elif fault=='cf_retained':row['sender_cf_released_before_go']=False
    elif fault=='handle_retained':row['sender_resource_handle_cleared']=False
    elif fault=='query_before_go':row['resource_query_before_go']=0
    elif fault=='disposition':row['initial_disposition']=19
    elif fault=='initial_query':row['initial_query']=0
    elif fault=='remote_type':row['remote_type_after_exit']=0
    elif fault=='control_type':row['control_type_after_exit']=0
    elif fault=='remote_cleanup':row['remote_query_after_release']=0
    elif fault=='control_cleanup':row['control_query_after_release']=0
    elif fault=='audit_ready':row['audit_ready_verified']=False
    elif fault=='audit_complete':row['audit_completion_verified']=False
    elif fault=='rendezvous':row['rendezvous_removed']=False
    elif fault=='child_pid':child['receiver_pid']=555
    elif fault=='mode':child['mode']=1
    elif fault=='small_code':child['small_code']=0
    elif fault=='full_code':child['full_code']=0
    elif fault=='queue':child['queued_after_small']=1
    elif fault=='false_id':child['surface_id']=row['surface_id']
    elif fault=='false_name':child['received_name']=999
    elif fault=='false_query':child['resource_query']=15
    elif fault=='audit_go':child['audit_go_verified']=False
    elif fault=='false_import':child['imported']=True
    elif fault=='false_audit':child['audit_resource_verified']=True
    elif fault=='alias_retained':child['alias_released']=False
    elif fault=='endpoint':child['inbox_query']=0
    elif fault in ['pixel','padding','tail','stale_mutation']:
     f=p/'owned-documents/move-control/receiver-mutated.bin';v=bytearray(f.read_bytes());v[{'pixel':0,'padding':68,'tail':16383,'stale_mutation':0}[fault]]^=0x5a if fault=='stale_mutation' else 1;f.write_bytes(v)
    elif fault=='extra_file':(folder/'receiver-first.bin').write_bytes(b'extra')
    elif fault=='missing_file':(folder/'sender-before.bin').unlink()
    elif fault=='typed':row['resource_query_before_go']=15.0
    cpath.write_text(json.dumps(child))
    if fault not in ['hash','bytes']:encode(r,rows)
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"sender_pid": 123','"sender_pid": 123, "sender_pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError)):admitted(p)
if __name__=='__main__':unittest.main()
