import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_source_stage_failure import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/source-stage-failure-2026-10-12'
class SourceStageFailureTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['source_write_failure_retained']);self.assertEqual((ROOT/'tools/re/reloop/rust_source_builder.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/source_stage_failure_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','caught','before','retained','diagnostic','writes','handoff','budget','files','source','log','scope','wait','jobs','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][4]
    if fault=='original':row['originalPreserved']=False
    elif fault=='caught':row['caught']='Error: Owned log failure ENOSPC'
    elif fault=='before':d['rows'][0]['failures']=[{'error':row['caught']}]
    elif fault=='retained':row['failures']=[]
    elif fault=='diagnostic':d['rows'][6]['failures'][0].pop('persistence_error')
    elif fault=='writes':row['logWrites']=0
    elif fault=='handoff':row['handoffs']=1
    elif fault=='budget':row['budget']['stagesCreated']=0
    elif fault=='files':row['files']=[]
    elif fault=='source':p=e/'after-execution'/d['rows'][7]['stage']/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='log':p=e/'after-ENOSPC'/row['stage']/'failure.json';d={'error':'Failure lost'}
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['actual_disk_full_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    elif fault=='jobs':d['actualCompilerJobs']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['after_source_failure_retained']=False
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='e6b5d72052ecfac2ee2f35a4279317d1730db8cb5f31b1d65a5bdd782b37f1a4'
