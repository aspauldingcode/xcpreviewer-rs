import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_bounded_build_history import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/bounded-build-history-2026-10-11'
class BoundedBuildHistoryTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['count_bound_verified']);self.assertEqual(hashlib.sha256((E/'rust-builder-after.js').read_bytes()).hexdigest(),'f06ac0c13a30ea13ccba93c9fa20b7995d290f3e6a3afb76dc8f22b841998deb');self.assertEqual((ROOT/'tools/re/tests/bounded_build_history_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['limit','dropped','oldest','newest','failure-order','retained','invalid','native','disk','budget','receipt','missing']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());r=next(x for x in d['results'] if x['phase']=='after' and x['name']=='default')
    if fault=='retained':p=e/'retained-failures'/r['retainedFailures'][0]['file'];d={'error':'Lost original failure'}
    elif fault=='disk':p=e/'scope.json';d=json.loads(p.read_text());d['raw_disk_quota_qualified']=True
    elif fault=='budget':p=e/'environment.json';d=json.loads(p.read_text());d['budgets']['node_seconds']=30
    elif fault=='limit':r['history']['limit']=65
    elif fault=='dropped':r['history']['recordsDropped']=0
    elif fault=='oldest':r['records'][0]['execution']['syntheticJobId']=1
    elif fault=='newest':r['records'][-1]['execution']['syntheticJobId']=127
    elif fault=='failure-order':r['failures'].reverse()
    elif fault=='invalid':d['invalid'][0]['rootCreated']=True
    elif fault=='native':d['actualCompilerJobs']=1
    elif fault=='receipt':r['records'][0]['receipt']['cache_hit']=True
    else:d['results'].pop()
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='2d447b717afc442f1443115938e8d1823dfd4d76830cb7bbe1246b612bbd75c3'
