import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('surface_reuse_reader',Path(__file__).with_name('verify_surface_full_reuse.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceFullReuseTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-full-reuse-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['full_allocation_bytes'],163840)
  for name in ['full_reuse_probe.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceFullReuse'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','audit','release','identity','recurrence','allocation','refs','retired','generation','active','padding','tail','old-frame']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-full-reuse-2026-10-11',e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()];q=e/'reuse/receiver.json';peer=json.loads(q.read_text())
    if fault=='exit':d['code']=51
    elif fault=='timeout':d['timeout']=True
    elif fault=='audit':rows[0]['audit_peer_verified']=False
    elif fault=='release':rows[0]['sender_aliases_released']=False
    elif fault=='identity':rows[0]['second_id']+=1
    elif fault=='recurrence':
     old=rows[1]['first_id'];new=old+1;rows[1]['first_id']=rows[1]['live_global_first']=new
     if rows[1]['final_global_first']==old:rows[1]['final_global_first']=new
     separate=e/'separate/receiver.json';other=json.loads(separate.read_text());other['first_id']=new;separate.write_text(json.dumps(other))
    elif fault=='allocation':rows[0]['allocation_bytes']=1152
    elif fault=='refs':peer['first_refs_after_two_imports']=1
    elif fault=='retired':peer['retired_first_lookup']=peer['first_id']
    elif fault=='generation':peer['fixture_generations']=[2,1]
    elif fault=='old-frame':shutil.copyfile(e/'reuse/producer-first.bin',e/'reuse/delayed-first.bin')
    else:
     rawpath=e/'reuse/after-right-release.bin';raw=bytearray(rawpath.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;rawpath.write_bytes(raw)
    d['stdout']=''.join(json.dumps(x)+'\n' for x in rows);p.write_text(json.dumps(d));q.write_text(json.dumps(peer));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='3882895c02cd09939282f3d1c8867c5726e236a094d4107617201afe39988d6a'
