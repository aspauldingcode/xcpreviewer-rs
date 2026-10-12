import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_callback_descendant_wait import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/callback-descendant-wait-2026-10-12'
class CallbackDescendantWaitTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['owned_child_reaped']);self.assertEqual((ROOT/'tools/re/fixtures/CallbackDescendantWait.py').read_bytes(),(E/'target.py').read_bytes());self.assertEqual((ROOT/'tools/re/tests/callback_descendant_wait_control.js').read_bytes(),(E/'control.js').read_bytes())
  self.assertEqual(hashlib.sha256((E/'observed_compiler.js').read_bytes()).hexdigest(),'3f781300f8931852f33520acff5768dba787d331d5bad42d20bfbe892216b99a')
  for name in ['observed_group_anchor.py']:self.assertEqual((ROOT/'tools/re/reloop'/name).read_bytes(),(E/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['original','abort','drain','parent-wait','remaining','tracked','group','identity','ack','child-wait','raw-wait','peer','alarm','scope','outer-wait','helper']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'native-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='original':d['originalPreserved']=False
    elif fault=='abort':rec['privateAbortRequested']=False
    elif fault=='drain':rec['report']['drained']=False
    elif fault=='parent-wait':rec['report']['target_code']=-15
    elif fault=='remaining':rec['report']['remaining_observed']=1
    elif fault=='tracked':rec['report']['tracked']=1
    elif fault=='group':d['trigger']['child']['group']=rec['pid']
    elif fault=='identity':d['trigger']['child']['identity'][2]='/wrong/python'
    elif fault=='ack':p=e/'native-0/ready.json';d=json.loads(p.read_text());d['child_ack']='missing'
    elif fault in ['child-wait','raw-wait']:p=e/'native-0/child-wait.json';d=json.loads(p.read_text());d['exit_code' if fault=='child-wait' else 'raw_status']=0
    elif fault=='peer':p=e/'native-0/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='alarm':p=e/'target.py';p.write_text(p.read_text().replace(' signal.alarm(6)\n',''));d=None
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['unseen_escapes_qualified']=True
    elif fault=='outer-wait':p=e/'wait-0.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='d8a4bf33aae07872af2b0b7c4788d74a9c91d38ae258919959057c8e8aa2c96c'
