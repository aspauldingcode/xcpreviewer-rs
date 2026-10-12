import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_failure_record_size import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/failure-record-size-2026-10-12'
class FailureRecordSizeTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['record_field_limit'],524288);self.assertEqual((ROOT/'tools/re/reloop/rust_source_builder.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/failure_record_size_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','caller','count','omission','diagnostic','under','exact','escape','budget','source','disk','scope','heap','wait','jobs','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][7]
    if fault=='original':row['originalPreserved']=False
    elif fault=='caller':row['originalRecordStillPresent']=False
    elif fault=='count':row['serializedBytes']=524288
    elif fault=='omission':row['failure']['record']={'payload':'x'}
    elif fault=='diagnostic':row['failure'].pop('record_error')
    elif fault=='under':d['rows'][5]['failure'].pop('record')
    elif fault=='exact':d['rows'][6]['failure']['record']['payload']+='x'
    elif fault=='escape':d['rows'][9]['serializedBytes']=100014
    elif fault=='budget':row['budget']['stagesCreated']=0
    elif fault=='source':p=e/'after-ascii-over'/row['stage']/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='disk':p=e/'after-ascii-over'/row['stage']/'failure.json';d={'error':'Lost omission diagnostic'}
    elif fault in ['scope','heap']:p=e/'scope.json';d=json.loads(p.read_text());d['total_heap_disk_quota_qualified' if fault=='scope' else 'initial_serialization_memory_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    elif fault=='jobs':d['actualCompilerJobs']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['limit_serialized_utf8_bytes']=1048576
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='f129bacdc8c6bc74fe0de12976814ee6806345ba23b433dbf88427e3c770897c'
