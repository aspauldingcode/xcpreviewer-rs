import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_stopped_child_exit import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/stopped-child-exit-2026-10-12'
class StoppedChildTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_marker_bytes'],16);self.assertEqual((ROOT/'tools/re/tests/stopped_child_exit_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes());self.assertEqual((ROOT/'tools/re/native/OwnedStoppedExitEvents.c').read_bytes(),(E/'OwnedStoppedExitEvents.c').read_bytes())
 def test_resealed_faults(self):
  for fault in ['stopped-status','running-status','stopped-request','birth','marker','stop','signal-data','ordinary-exit','order','receipt','abort','root-code','watcher-wait','erased-failure','failed-producer-success','prediction','revised','reaped','helper','watcher-hash','build','slots']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'stopped-1/registered.json';d=json.loads(p.read_text())
    if fault=='stopped-status':d['child_status']=2
    elif fault=='running-status':p=e/'running-0/registered.json';d=json.loads(p.read_text());d['child_status']=4
    elif fault=='stopped-request':d['stopped_requested']=False
    elif fault=='birth':d['birth_rechecked']=False
    elif fault=='marker':p=e/'stopped-1/stopped-marker.raw';p.write_bytes(b'wrong');d=None
    elif fault=='stop':p=e/'stopped-1/stop';p.write_text('wrong');d=None
    elif fault in ['signal-data','ordinary-exit','order']:p=e/'stopped-1/kernel-exit-events.json';d=json.loads(p.read_text());d.reverse() if fault=='order' else None;d[1]['data']=9 if fault=='signal-data' else d[1]['data'];d[1]['exited']=True if fault=='ordinary-exit' else d[1]['exited']
    elif fault=='receipt':p=e/'stopped-1/result.json';d=json.loads(p.read_text());d['record']['report']=None
    elif fault=='abort':p=e/'stopped-1/result.json';d=json.loads(p.read_text());d['record']['privateAbortRequested']=True
    elif fault=='root-code':p=e/'stopped-1/result.json';d=json.loads(p.read_text());d['record']['report']['target_code']=0
    elif fault=='watcher-wait':p=e/'stopped-1/watcher-wait.json';d=json.loads(p.read_text());d['status']=1
    elif fault=='erased-failure':p=e/'stopped-0/retained-failure.json';d=json.loads(p.read_text());d['error']='pass'
    elif fault=='failed-producer-success':p=e/'wait-stopped-0.json';d=json.loads(p.read_text());d['code']=0
    elif fault=='prediction':p=e/'prediction.json';d=json.loads(p.read_text());d['child_raw_statuses']=[15]*4
    elif fault=='revised':p=e/'revised-prediction.json';d=json.loads(p.read_text());d['child_raw_statuses']=[9,9,15,15]
    elif fault=='reaped':p=e/'scope.json';d=json.loads(p.read_text());d['child_reaped_qualified']=True
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='watcher-hash':p=e/'watcher.json';d=json.loads(p.read_text());d['sha256']='0'*64
    elif fault=='build':p=e/'build.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'slots.json';d=json.loads(p.read_text());d['used']=5
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='098288db1efb95f508f8c6da7e30bcf9d00e065357bdc5d53521a9f4db8d670b'
