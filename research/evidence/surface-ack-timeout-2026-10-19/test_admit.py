import unittest,tempfile,json,hashlib,shutil
from pathlib import Path
from admit import admitted
from phase_gate import dispatch
base=Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-preimport-cancel-2026-10-19')
class Controls(unittest.TestCase):
 def fixture(self,r):
  shutil.copy2(Path(__file__).parent/'probe.c',r/'probe.c');old=json.loads((base/'fixture-record.json').read_text());rows=[json.loads(x) for x in old['record']['stdout'].splitlines()];out=[]
  for i,j in enumerate([0,2]):
   row=rows[j];row.update(mode=i,initial_move=True,initial_disposition=17,initial_query=15,ack_receive_code=268451843 if i else 0,ack_queue_before_timeout=0,ack_queue_after_timeout=0,audit_release_verified=True,audit_withheld_verified=bool(i),late_ack_verified=bool(i));out.append(row)
   src=base/'owned-documents'/('copy-import' if i==0 else 'move-import');dst=r/'owned-documents'/('move-timely' if i==0 else 'move-withheld');shutil.copytree(src,dst);f=dst/'receiver.json';child=json.loads(f.read_text());child.update(mode=i,resource_released_before_ack_decision=True,withheld_until_retry=bool(i));f.write_text(json.dumps(child))
  raw=''.join(json.dumps(x)+'\n' for x in out);old['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest());old['source_sha256']=hashlib.sha256((r/'probe.c').read_bytes()).hexdigest();(r/'fixture-record.json').write_text(json.dumps(old))
  for name in ['fixture-outer.json','compile-record.json','compile-outer.json','output-valid-record.json','output-valid-outer.json']:shutil.copy2(base/name,r/name)
  for name in ['compile-record.json','output-valid-record.json']:
   f=r/name;v=json.loads(f.read_text());v['source_sha256']=old['source_sha256'];f.write_text(json.dumps(v))
 def test_positive(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);self.fixture(r);self.assertEqual(admitted(r)['full_bytes_compared'],131072)
 def test_parent_faults(self):
  for field,value in [('ack_receive_code',0),('audit_release_verified',False),('audit_withheld_verified',False),('late_ack_verified',False),('receiver_exit',1),('ack_queue_after_timeout',1),('mode',True)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'fixture-record.json';v=json.loads(f.read_text());rows=[json.loads(x) for x in v['record']['stdout'].splitlines()];rows[1][field]=value;raw=''.join(json.dumps(x)+'\n' for x in rows);v['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest());f.write_text(json.dumps(v))
    with self.assertRaises(ValueError):admitted(r)
 def test_child_faults(self):
  for field,value in [('resource_released_before_ack_decision',False),('withheld_until_retry',False),('alias_release_observed',False),('resource_query',0),('resource_refs_before_destroy',True)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'owned-documents/move-withheld/receiver.json';v=json.loads(f.read_text());v[field]=value;f.write_text(json.dumps(v))
    with self.assertRaises(ValueError):admitted(r)
 def test_allocation_regions(self):
  for offset in [0,68,16383]:
   with self.subTest(offset=offset),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'owned-documents/move-withheld/receiver-mutated.bin';v=bytearray(f.read_bytes());v[offset]^=1;f.write_bytes(v)
    with self.assertRaises(ValueError):admitted(r)
 def test_prerequisite_dispatch(self):
  for fault in ['missing','failed','tampered','none']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);(r/'probe').write_bytes(b'synthetic owned binary');h=hashlib.sha256((r/'probe').read_bytes()).hexdigest()
    for name in ['compile-record.json','output-valid-record.json']:
     f=r/name;v=json.loads(f.read_text());v['binary_sha256']=h;f.write_text(json.dumps(v))
    if fault=='missing':(r/'output-valid-record.json').unlink()
    if fault=='failed':
     f=r/'compile-outer.json';v=json.loads(f.read_text());v['node_exit']=1;f.write_text(json.dumps(v))
    if fault=='tampered':
     f=r/'output-valid-record.json';v=json.loads(f.read_text());v['source_sha256']='0'*64;f.write_text(json.dumps(v))
    called=[]
    if fault=='none':dispatch(r,'fixture',lambda:called.append(1));self.assertEqual(called,[1])
    else:
     with self.assertRaises(ValueError):dispatch(r,'fixture',lambda:called.append(1))
     self.assertEqual(called,[])
 def test_fixture_binding(self):
  for field in ['source_sha256','phase']:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'fixture-record.json';v=json.loads(f.read_text());v[field]='bad';f.write_text(json.dumps(v))
    with self.assertRaises(ValueError):admitted(r)
if __name__=='__main__':unittest.main()
