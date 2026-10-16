import hashlib,json,tempfile,unittest
from pathlib import Path
from admit import admitted

def encode(r,rows):
 raw=''.join(json.dumps(x)+'\n' for x in rows);r['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
def build(p):
 r={'error':None,'binary_sha256':'a'*64,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stderr':'owned_tree_pid:123\n'}};rows=[]
 for index in range(3):
  rows.append(dict(pid=123,mode=index,imported=(index!=2),receive_code=268451843 if index==2 else 0,small_code=268451844 if index else 0,transfer_size=64,header_size=24,queued_before=1,queued_after=0 if index==2 else 1,queued_final=0,refs_before=1,refs_after=1,refs_received=1 if index==2 else 2,refs_destroyed=1,remaining_refs=0,resource_name=55+index,received_name=0 if index==2 else 55+index,resource_query_after=15,endpoint_query_after=15,endpoint_removed=True,stride=128,allocation_bytes=16384))
  d=p/'owned-documents'/(['control','large','small'][index]);d.mkdir(parents=True)
  data=bytearray([0xa5]*16384)
  for y in range(9):
   for x in range(17):data[y*128+x*4:y*128+x*4+4]=bytes([(49+x*17+y*31)&255,(102+x*17+y*31)&255,(155+x*17+y*31)&255,255])
  for name in ['before.bin','after-small.bin','after-empty-receive.bin' if index==2 else 'received.bin','alias-after-cleanup.bin']:(d/name).write_bytes(data)
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class ReceiveSizeTests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);build(p);self.assertEqual(admitted(p)['full_bytes_compared'],196608)
 def test_faults(self):
  for fault in ['wait','drain','remaining','abort','binary','bytes','hash','pid','missing','code','size','queue','refs','removal','name','bool','receive_code','false_import','extra_branch_file','missing_branch_file','padding','tail','pixel','duplicate']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);r,rows=build(p);row=rows[2]
    if fault=='wait':r['record']['report']['target_code']=1
    elif fault=='drain':r['record']['report']['drained']=False
    elif fault=='remaining':r['record']['report']['remaining_observed']=1
    elif fault=='abort':r['record']['privateAbortRequested']=True
    elif fault=='binary':r['binary_sha256']='b'*64
    elif fault=='bytes':r['record']['stdoutBytes']+=1
    elif fault=='hash':r['record']['stdoutSha256']='0'*64
    elif fault=='pid':row['pid']=124
    elif fault=='missing':rows.pop()
    elif fault=='code':row['small_code']=0
    elif fault=='size':row['transfer_size']=24
    elif fault=='queue':row['queued_after']=1
    elif fault=='refs':row['refs_received']=2
    elif fault=='removal':row['resource_query_after']=0
    elif fault=='name':row['received_name']+=1
    elif fault=='bool':row['refs_before']=True
    elif fault=='receive_code':row['receive_code']=0
    elif fault=='false_import':row['imported']=True
    elif fault=='extra_branch_file':(p/'owned-documents/small/received.bin').write_bytes(b'extra')
    elif fault=='missing_branch_file':(p/'owned-documents/small/after-empty-receive.bin').unlink()
    elif fault in ['padding','tail','pixel']:
     f=p/'owned-documents/small/after-empty-receive.bin';v=bytearray(f.read_bytes());v[{'padding':68,'tail':16383,'pixel':0}[fault]]^=1;f.write_bytes(v)
    if fault not in ['bytes','hash']:encode(r,rows)
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"pid": 123','"pid": 123, "pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError)):admitted(p)
if __name__=='__main__':unittest.main()
