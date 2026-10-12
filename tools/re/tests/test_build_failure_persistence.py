import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_build_failure_persistence import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/build-failure-persistence-2026-10-12'
class BuildFailurePersistenceTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['original_error_preserved']);self.assertEqual(hashlib.sha256((E/'after.js').read_bytes()).hexdigest(),'f6c739354d4483d9170d7395d7a4a67311d2521f486193c59b94b3084932d51b');self.assertEqual((ROOT/'tools/re/tests/build_failure_persistence_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','caught','before','diagnostic','failure','record','writes','persisted','budget','source','normal-log','scope','wait','jobs','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][4]
    if fault=='original':row['originalPreserved']=False
    elif fault=='caught':row['caught']='Error: Owned failure log ENOSPC'
    elif fault=='before':d['rows'][1]['originalPreserved']=True
    elif fault=='diagnostic':row['failure'].pop('persistence_error')
    elif fault=='failure':row['failure']['error']='Failure lost'
    elif fault=='record':row['failure']['record']['id']=0
    elif fault=='writes':row['writes']=0
    elif fault=='persisted':row['persisted']=True
    elif fault=='budget':row['budget']['stagesCreated']=0
    elif fault=='source':p=e/'after-ENOSPC'/row['stage']/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='normal-log':p=e/'after-normal'/d['rows'][3]['stage']/'failure.json';d={'error':'Lost original'}
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['actual_disk_full_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    elif fault=='jobs':d['actualCompilerJobs']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['after_original_error_preserved']=False
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='c0fe65571470bfa61987d9e5ac2f15e5d798e1c6adecfdb7f61eb4ecf72ac755'
