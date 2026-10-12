import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_overflow_control_drain import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/overflow-control-drain-2026-10-12'
class OverflowControlDrainTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_peer_bytes'],24);self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/overflow_control_drain_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['abort','receipt','emergency','underlying','child-wait','peer','hash','write','fd','quota','cleanup','stdout-byte','stdout-limit','identity','outer-wait','helper','runtime','slots']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'control-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='abort':rec['privateAbortRequested']=False
    elif fault=='receipt':rec['report']=json.loads((e/'control-0/underlying-complete.json').read_text())
    elif fault=='emergency':rec['emergencyClosed']=False
    elif fault=='underlying':p=e/'control-0/underlying-complete.json';d=json.loads(p.read_text());d['target_code']=0
    elif fault=='child-wait':p=e/'control-0/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    elif fault=='peer':p=e/'control-0/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault in ['hash','identity']:p=e/'control-0/injection.json';d=json.loads(p.read_text());d['payload_sha256']='0'*64 if fault=='hash' else d['payload_sha256'];d['original']['rows'][0]['identity'][2]='/wrong/python' if fault=='identity' else d['original']['rows'][0]['identity'][2]
    elif fault in ['write','fd']:p=e/'control-0/injection-write.json';d=json.loads(p.read_text());d['written_bytes' if fault=='write' else 'fd']=0
    elif fault in ['quota','cleanup','slots']:p=e/'scope.json';d=json.loads(p.read_text());d['control_quota_reset' if fault=='quota' else 'control_client_cleanup_receipt_qualified' if fault=='cleanup' else 'producer_slots_used']=True if fault!='slots' else 5
    elif fault in ['stdout-byte','stdout-limit']:p=e/'stdout/result.json';d=json.loads(p.read_text());d['record']['stdout']='y' if fault=='stdout-byte' else 'x'*65537
    elif fault=='outer-wait':p=e/'wait-control-0.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    else:p=e/'environment.json';d=json.loads(p.read_text());d['runtime_sha256']='0'*64
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='f912ccc642f95e5e7cee8dc33eeee977b6295cf628bff138e853e3cb33852306'
