import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('global_id_reader',Path(__file__).with_name('verify_surface_global_id.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceGlobalIDTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-global-id-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],73)
  for name in ['global_id_probe.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceGlobalID'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','held-right','owner','before','match','ids','cleanup','settled','missing','active','padding','tail','stale-old']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-global-id-2026-10-11',e);root=e/'held';p=root/'wait.json';d=json.loads(p.read_text());row=json.loads(d['stdout'])
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='held-right':row['right_refs_during_churn']=0
    elif fault=='owner':row['owner_cf_released']=False
    elif fault=='before':row['before_lookup_present']=False
    elif fault=='match':row['matched']=True
    elif fault=='ids':row['candidate_ids'][0]=row['old_id']
    elif fault=='cleanup':row['port_released']=False
    elif fault=='settled':row['settled_lookup_present']=True
    elif fault=='missing':(root/'candidate-063.bin').unlink()
    elif fault=='stale-old':shutil.copyfile(e/'released-0/initial.bin',e/'released-0/stale-lookup.bin')
    else:
     q=root/'retained-lookup.bin';raw=bytearray(q.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;q.write_bytes(raw)
    d['stdout']=json.dumps(row)+'\n';p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='bd226026918aad2d7e4bc14e83fc1c733bad99ec023b90f64a7f59f22d902200'
