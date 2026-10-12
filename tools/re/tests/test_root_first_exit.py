import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_root_first_exit import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/root-first-exit-2026-10-12'
class RootFirstExitTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_peer_bytes'],32);self.assertEqual((ROOT/'tools/re/tests/root_first_exit_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes());self.assertEqual((ROOT/'tools/re/native/OwnedExitEvents.c').read_bytes(),(E/'OwnedExitEvents.c').read_bytes())
 def test_resealed_faults(self):
  for fault in ['error','success-error','abort','receipt','emergency','root-wait','failure-reason','tracked','child-event','peer','empty-digest','intent','release','identity','finish','outer-wait','helper','runtime','slots','reaped-claim','event-order','event-status','event-filter','registered','watcher-wait','build','build-failure','watcher-hash']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'failure-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='error':d['error']=None
    elif fault=='success-error':p=e/'success-0/result.json';d=json.loads(p.read_text());d['error']='Error: failure'
    elif fault=='abort':rec['privateAbortRequested']=True
    elif fault=='receipt':rec['report']=None
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='root-wait':rec['report']['target_code']=0
    elif fault=='failure-reason':rec['report']['failure']='abort'
    elif fault=='tracked':rec['report']['tracked']=1
    elif fault=='child-event':p=e/'failure-0/kernel-exit-events.json';d=json.loads(p.read_text());d[1]['data']=0
    elif fault=='peer':p=e/'failure-0/child.raw';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);d=None
    elif fault=='empty-digest':rec['stdoutSha256']='0'*64
    elif fault=='intent':p=e/'failure-0/exit-intent.json';d=json.loads(p.read_text());d['without_child_wait']=False
    elif fault=='release':d['released']=False
    elif fault=='identity':p=e/'failure-0/release-observation.json';d=json.loads(p.read_text());d[0]['identity'][2]='/wrong/python'
    elif fault=='finish':p=e/'failure-0/finish';p.write_text('wrong');d=None
    elif fault=='outer-wait':p=e/'wait-failure-0.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='runtime':p=e/'environment.json';d=json.loads(p.read_text());d['runtime_sha256']='0'*64
    elif fault=='slots':p=e/'slots.json';d=json.loads(p.read_text());d['used']=5
    elif fault=='reaped-claim':p=e/'prediction.json';d=json.loads(p.read_text());d['child_reaped_qualified']=True
    elif fault in ['event-order','event-status','event-filter']:p=e/'failure-0/kernel-exit-events.json';d=json.loads(p.read_text());d.reverse() if fault=='event-order' else None;d[1]['fflags']=2147483648 if fault=='event-status' else d[1]['fflags'];d[1]['filter']=0 if fault=='event-filter' else d[1]['filter']
    elif fault=='registered':p=e/'failure-0/registered.json';d=json.loads(p.read_text());d['birth_rechecked']=False
    elif fault=='watcher-wait':p=e/'failure-0/watcher-wait.json';d=json.loads(p.read_text());d['status']=100
    elif fault=='build':p=e/'build.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='build-failure':p=e/'build-before.json';d=json.loads(p.read_text());d['code']=0
    else:p=e/'watcher.json';d=json.loads(p.read_text());d['sha256']='0'*64
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='4d718c087765d5e2d4a504167d9e82b01ea97fe1dcf0209f6fda823a4dc841dc'
