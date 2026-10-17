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
 for mode in range(3):
  row=dict(sender_pid=123,receiver_pid=124+mode,mode=mode,surface_id=50+mode,receiver_exit=0,sender_refs_before=1,sender_refs_after_error=1,sender_refs_after_retry=1,sender_refs_after_exit=1,sender_removed_query=15,rendezvous_removed=True,audit_ready_verified=True,audit_stage1_verified=True,audit_stage3_verified=True);rows.append(row)
  folder=p/'owned-documents'/['control','large','small'][mode];folder.mkdir(parents=True)
  child=dict(receiver_pid=124+mode,parent_pid=123,mode=mode,small_code=0 if mode==0 else 268451844,full_code=268451843 if mode==2 else 0,queued_before=1,queued_after_small=0 if mode==2 else 1,queued_final=0,first_id=0 if mode==2 else 50+mode,retry_id=50+mode,first_name=0 if mode==2 else 901,retry_name=902,first_query=0 if mode==2 else 15,retry_query=15,endpoint_query=15,imported_right_refs=1,audit_retry_verified=True,audit_first_verified=mode!=2)
  (folder/'receiver.json').write_text(json.dumps(child))
  for name in ['sender-before.bin','sender-after-error.bin','sender-mutated.bin','sender-after-exit.bin','receiver-retry.bin','receiver-after-right-release.bin']+(['receiver-first.bin'] if mode!=2 else []):(folder/name).write_bytes(base if name in ['sender-before.bin','sender-after-error.bin','receiver-first.bin'] else changed)
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class AdmissionTests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);build(p);self.assertEqual(admitted(p)['full_bytes_compared'],327680)
 def test_faults(self):
  for fault in ['wait','drain','remaining','abort','binary','hash','bytes','sender_pid','peer_pid','peer_exit','sender_refs','sender_remove','audit','child_pid','mode','queue','small_code','full_code','retry_id','false_first_id','first_name','retry_name','first_query','retry_query','endpoint_query','import_refs','audit_retry','audit_first','typed','pixel','padding','tail','stale_mutation','extra_file','missing_file','duplicate']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);r,rows=build(p);row=rows[2];folder=p/'owned-documents/small';cpath=folder/'receiver.json';child=json.loads(cpath.read_text())
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
    elif fault=='sender_refs':row['sender_refs_after_error']=2
    elif fault=='sender_remove':row['sender_removed_query']=0
    elif fault=='audit':row['audit_stage1_verified']=False
    elif fault=='child_pid':child['receiver_pid']=555
    elif fault=='mode':child['mode']=1
    elif fault=='queue':child['queued_after_small']=1
    elif fault=='small_code':child['small_code']=0
    elif fault=='full_code':child['full_code']=0
    elif fault=='retry_id':child['retry_id']+=1
    elif fault=='false_first_id':child['first_id']=row['surface_id']
    elif fault=='first_name':child['first_name']=999
    elif fault=='retry_name':child['retry_name']=0
    elif fault=='first_query':child['first_query']=15
    elif fault=='retry_query':child['retry_query']=0
    elif fault=='endpoint_query':child['endpoint_query']=0
    elif fault=='import_refs':child['imported_right_refs']=2
    elif fault=='audit_retry':child['audit_retry_verified']=False
    elif fault=='audit_first':child['audit_first_verified']=True
    elif fault=='typed':child['retry_id']=float(child['retry_id'])
    elif fault in ['pixel','padding','tail']:
     f=folder/'receiver-retry.bin';v=bytearray(f.read_bytes());v[{'pixel':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(v)
    elif fault=='stale_mutation':(folder/'receiver-retry.bin').write_bytes((folder/'sender-before.bin').read_bytes())
    elif fault=='extra_file':(folder/'receiver-first.bin').write_bytes(b'extra')
    elif fault=='missing_file':(folder/'receiver-retry.bin').unlink()
    cpath.write_text(json.dumps(child))
    if fault not in ['hash','bytes']:encode(r,rows)
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"sender_pid": 123','"sender_pid": 123, "sender_pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError)):admitted(p)
if __name__=='__main__':unittest.main()
