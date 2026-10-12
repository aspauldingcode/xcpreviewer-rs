import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('surface_full_reader',Path(__file__).with_name('verify_surface_full_failure.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceFullFailureTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-full-failure-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['full_allocation_bytes'],65536)
  for name in ['full_failure_probe.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceFullFailure'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','completion','audit','rights','cleanup','peer','signal','allocation','active','padding','tail']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-full-failure-2026-10-11',e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()]
    if fault=='exit':d['code']=43
    elif fault=='timeout':d['timeout']=True
    elif fault=='completion':rows[1]['completion_accepted']=True
    elif fault=='audit':rows[1]['audit_peer_verified']=False
    elif fault=='rights':rows[1]['local_resource_refs_retained']=0
    elif fault=='cleanup':rows[1]['local_resource_name_removed']=False
    elif fault=='peer':rows[1]['receiver_pid']=rows[0]['receiver_pid']
    elif fault=='signal':rows[1]['peer_signal']=0
    elif fault=='allocation':rows[1]['allocation_bytes']=1152
    else:
     q=e/'before-ack/retained.bin';raw=bytearray(q.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;q.write_bytes(raw)
    d['stdout']=''.join(json.dumps(x)+'\n' for x in rows);p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='e6d6c1cb5bac06343c547dcfe0b633908b43ef900b511c8a2c03d9b85f332a72'
