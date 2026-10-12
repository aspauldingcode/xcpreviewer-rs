import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_preabort_build_staging import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/preabort-build-staging-2026-10-11'
class PreabortBuildStagingTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['prestage_cancel_verified']);self.assertEqual(hashlib.sha256((E/'rust-builder-after.js').read_bytes()).hexdigest(),'1f8abc8d09290e14a81012d51ef3106af401815b0873ec8e89c632cda13aabba');self.assertEqual((ROOT/'tools/re/tests/preabort_build_staging_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['spawns','errors','stages','bytes','pre-spawn','positive','records','disk-source','failure','scope','budget','missing']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['results'][1]
    if fault=='disk-source':p=e/'before'/d['results'][0]['preStages'][0]/'source.swift';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='failure':p=e/'after'/row['finalStages'][0]/'failure.json';d={'error':'Hidden failure'}
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['actual_compiler_cancel_qualified']=True
    elif fault=='budget':p=e/'environment.json';d=json.loads(p.read_text());d['budgets']['node_seconds']=20
    elif fault=='spawns':d['actualChildSpawns']=1
    elif fault=='errors':row['errors'][0]='Error: Observed compiler aborted before spawn'
    elif fault=='stages':row['preStages']=row['finalStages']
    elif fault=='bytes':row['preStagedSourceBytes']=202
    elif fault=='pre-spawn':row['preSpawnCount']=1
    elif fault=='positive':row['interceptedNoncancelledSpawns']=0
    elif fault=='records':row['records']=[{'accepted':True}]
    else:d['results'].pop()
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='91446a3a2583afec7746c25f28ac74f0c99b6d597a8da53a686d9d342f59427d'
