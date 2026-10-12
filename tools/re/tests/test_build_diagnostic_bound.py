import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_build_diagnostic_bound import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/build-diagnostic-bound-2026-10-12'
class BuildDiagnosticBoundTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['failure_controls'],12);self.assertEqual(hashlib.sha256((E/'after.js').read_bytes()).hexdigest(),'a046fce2c6eff3ae516de5e6c2e06d8e66e092f212154336d2f5ed661116213d');self.assertEqual((ROOT/'tools/re/tests/build_diagnostic_bound_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','excerpt','boundary','count','metadata','log','before','writes','budget','source','disk','scope','wait','jobs','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][9]
    if fault=='original':row['originalPreserved']=False
    elif fault=='excerpt':row['failure']['error']=d['rows'][3]['failure']['error']
    elif fault=='boundary':row['failure']['error']+='�'
    elif fault=='count':row['originalBytes']=1024
    elif fault=='metadata':row['failure'].pop('error_original_bytes')
    elif fault=='log':d['rows'][11]['failure'].pop('persistence_error_original_bytes')
    elif fault=='before':d['rows'][3]['failure']['error']=row['failure']['error']
    elif fault=='writes':row['writes']=0
    elif fault=='budget':row['budget']['stagesCreated']=0
    elif fault=='source':p=e/'after-emoji'/row['stage']/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='disk':p=e/'after-emoji'/row['stage']/'failure.json';d={'error':'Failure lost'}
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['execution_record_byte_quota_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    elif fault=='jobs':d['actualCompilerJobs']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['error_limit_bytes']=2048
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='b6d4ddae8dc190e645efc08292a410040bcfc62843203e5f0ccf04f0da4d4645'
