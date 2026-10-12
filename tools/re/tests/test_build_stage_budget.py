import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_build_stage_budget import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/build-stage-budget-2026-10-11'
class BuildStageBudgetTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['per_builder_budget_verified']);self.assertEqual(hashlib.sha256((E/'rust-builder-after.js').read_bytes()).hexdigest(),'00cead97e7669e44edd973a33b19673fb2a47ecadc38cc49102607047756228b');self.assertEqual((ROOT/'tools/re/tests/build_stage_budget_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['pre-charge','limit','count','handoff','retry','failure','source','sentinel','invalid','global','deleted','native']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());r=d['results'][1]
    if fault in ['source','sentinel']:
     p=e/'after'/r['files'][0]['stage']/'source.swift' if fault=='source' else e/'after/unrelated.sentinel';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='failure':p=e/'after'/r['files'][0]['stage']/'failure.json';d={'error':'Original failure lost'}
    elif fault in ['global','deleted']:
     p=e/'scope.json';d=json.loads(p.read_text());d['cross_instance_root_quota_qualified' if fault=='global' else 'deleted_artifacts']=True if fault=='global' else 1
    elif fault=='pre-charge':r['preBudget']['stagesCreated']=1
    elif fault=='limit':r['budget']['stageLimit']=3
    elif fault=='count':r['budget']['stagesCreated']=1
    elif fault=='handoff':r['syntheticHandoffs']=3
    elif fault=='retry':r['retryError']=None
    elif fault=='invalid':d['invalid'][0]['rootCreated']=True
    else:d['actualCompilerJobs']=1
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='02a8a49dc0c888ce50ff0e641165a708f494be12ed3f861510bed018d5df852f'
