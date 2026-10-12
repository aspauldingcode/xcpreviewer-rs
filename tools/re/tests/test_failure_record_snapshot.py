import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_failure_record_snapshot import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/failure-record-snapshot-2026-10-12'
class FailureRecordSnapshotTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['snapshot_preserved']);self.assertEqual((ROOT/'tools/re/reloop/rust_source_builder.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/failure_record_snapshot_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','getter','snapshot','before','read','diagnostic','metadata','budget','files','source','disk','scope','wait','jobs','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][5]
    if fault=='original':row['originalPreserved']=False
    elif fault=='getter':d['rows'][8]['caught']='Error: Owned record getter failure'
    elif fault=='snapshot':row['failures'][0]['record']['value']=2
    elif fault=='before':d['rows'][0]['failures'][0]['record']['value']=1
    elif fault=='read':d['rows'][6]['readError']='Circular failure'
    elif fault=='diagnostic':d['rows'][6]['failures'][0]['record_error']='Failure lost'
    elif fault=='metadata':d['rows'][9]['failures'][0]['record_error']='Unexpected'
    elif fault=='budget':row['budget']['stagesCreated']=0
    elif fault=='files':row['files']=['source.swift']
    elif fault=='source':p=e/'after-mutable'/row['stage']/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='disk':p=e/'after-mutable'/row['stage']/'failure.json';d={'error':'Failure lost'}
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['record_byte_quota_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    elif fault=='jobs':d['actualCompilerJobs']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['after_mutation_stable']=False
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='3a627bc4f43ce8317d50bfa53fc41b382e0757c5138c7033c69f9e27c08e4c6b'
