import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_observer_callback_drain import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/observer-callback-drain-2026-10-12'
class ObserverCallbackDrainTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['sampled_drained']);self.assertEqual(hashlib.sha256((E/'after.js').read_bytes()).hexdigest(),'3f781300f8931852f33520acff5768dba787d331d5bad42d20bfbe892216b99a');self.assertEqual((ROOT/'tools/re/tests/observer_callback_drain_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_group_anchor.py').read_bytes(),(E/'observed_group_anchor.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','callback','abort','drain','wait','remaining','emergency','signal','parent','identity','before','scope','helper','outer-wait','late']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'native-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='original':d['originalPreserved']=False
    elif fault=='callback':d['callbacks']=0
    elif fault=='abort':rec['privateAbortRequested']=False
    elif fault=='drain':rec['report']['drained']=False
    elif fault=='wait':rec['report']['target_code']=0
    elif fault=='remaining':rec['report']['remaining_observed']=1
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='signal':rec['signal']='SIGTERM'
    elif fault=='parent':d['observed'][0][0]['parent']+=1
    elif fault=='identity':d['observed'][0][0]['identity'][2]='/wrong/python'
    elif fault=='before':p=e/'protocol-before/result.json';d=json.loads(p.read_text());d['record']['report']=rec['report']
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['unseen_escapes_qualified']=True
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='outer-wait':p=e/'wait-0.json';d=json.loads(p.read_text());d['code']=1
    else:(e/'native-0/late').write_text('late');d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='41fe2e6bf61667bbf825e35b5a450c65a36114e709813eea29a3f1300a18472f'
