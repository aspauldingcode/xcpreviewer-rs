import unittest,tempfile,json,copy,hashlib,shutil
from pathlib import Path
from admit import admitted
base=Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-queue-owner-2026-10-17')
class Controls(unittest.TestCase):
 def fixture(self,root):
  shutil.copy2(Path(__file__).parent/'probe.c',root/'probe.c');original=json.loads((base/'fixture-record.json').read_text());rows=[json.loads(x) for x in original['record']['stdout'].splitlines()];selected=[]
  for i,oldindex in enumerate([0,1,3,4]):
   move=i>=2;mode=i%2;row=rows[oldindex];row['mode']=mode;selected.append(row);old=base/'owned-documents'/(('move-' if move else 'copy-')+('control' if mode==0 else 'large'));new=root/'owned-documents'/(('move-' if move else 'copy-')+('import' if mode==0 else 'cancel'));new.mkdir(parents=True)
   for name in ['sender-before.bin']+(['receiver-first.bin','receiver-after-right-release.bin','receiver-mutated.bin'] if mode==0 else []):shutil.copy2(old/name,new/name)
   child=json.loads((old/'receiver.json').read_text());child={k:v for k,v in child.items() if k not in ['small_code','queued_after_small','alias_released']};child.update(mode=mode,queued_before_full=1,resource_refs_before_destroy=1,imported=mode==0,alias_acquired=mode==0,alias_release_observed=mode==0,cancel_before_import=mode==1);(new/'receiver.json').write_text(json.dumps(child))
  raw=''.join(json.dumps(x)+'\n' for x in selected);original['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest());(root/'fixture-record.json').write_text(json.dumps(original));shutil.copy2(base/'compile-record.json',root/'compile-record.json')
  for name in ['compile-outer.json','output-valid-record.json','output-valid-outer.json']:shutil.copy2(base/name,root/name)
  for name in ['compile-record.json','output-valid-record.json']:
   f=root/name;v=json.loads(f.read_text());v['source_sha256']=hashlib.sha256((root/'probe.c').read_bytes()).hexdigest();f.write_text(json.dumps(v))
 def test_positive(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);self.fixture(r);self.assertEqual(admitted(r)['full_bytes_compared'],163840)
 def test_faults(self):
  for field,value in [('cancel_before_import',False),('imported',True),('alias_acquired',True),('alias_release_observed',True),('resource_query',0),('resource_refs_before_destroy',True),('full_code',1),('audit_resource_verified',False),('parent_pid',1),('received_name',0),('inbox_query',0)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'owned-documents/copy-cancel/receiver.json';v=json.loads(f.read_text());v[field]=value;f.write_text(json.dumps(v))
    with self.assertRaises(ValueError):admitted(r)
 def test_every_allocation_region(self):
  for offset in [0,68,16383]:
   with self.subTest(offset=offset),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'owned-documents/copy-import/sender-before.bin';v=bytearray(f.read_bytes());v[offset]^=1;f.write_bytes(v)
    with self.assertRaises(ValueError):admitted(r)
 def test_prerequisite_dispatch(self):
  from phase_gate import dispatch
  for fault in ['missing','failed','tampered','none']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);(r/'probe').write_bytes(b'owned synthetic binary');binary=hashlib.sha256((r/'probe').read_bytes()).hexdigest()
    for name in ['compile-record.json','output-valid-record.json']:
     f=r/name;v=json.loads(f.read_text());v['binary_sha256']=binary;f.write_text(json.dumps(v))
    if fault=='missing':(r/'output-valid-record.json').unlink()
    if fault=='failed':
     f=r/'output-valid-outer.json';v=json.loads(f.read_text());v['node_exit']=1;f.write_text(json.dumps(v))
    if fault=='tampered':
     f=r/'output-valid-record.json';v=json.loads(f.read_text());v['source_sha256']='0'*64;f.write_text(json.dumps(v))
    called=[]
    if fault=='none':self.assertEqual(dispatch(r,'fixture',lambda:called.append(1)),None);self.assertEqual(called,[1])
    else:
     with self.assertRaises(ValueError):dispatch(r,'fixture',lambda:called.append(1))
     self.assertEqual(called,[])
if __name__=='__main__' :unittest.main()
