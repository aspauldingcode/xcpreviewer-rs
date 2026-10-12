import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_child_signal_exit import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/child-signal-exit-2026-10-12'
class ChildSignalTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_peer_bytes'],16);self.assertEqual((ROOT/'tools/re/tests/child_signal_exit_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes());self.assertEqual((ROOT/'tools/re/native/OwnedExitEvents.c').read_bytes(),(E/'OwnedExitEvents.c').read_bytes())
 def test_resealed_faults(self):
  for fault in ['signal-data','signal-as-exit','signal-code','handler-data','order','event-status','report','root-code','abort','peer','default-peer','watcher-wait','registered','reaped','aa','startup-accept','startup-wait','helper','runtime','slots']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'default-1/kernel-exit-events.json';d=json.loads(p.read_text())
    if fault=='signal-data':d[1]['data']=10752
    elif fault=='signal-as-exit':d[1]['exited']=True
    elif fault=='signal-code':d[1]['exit_code']=15
    elif fault=='handler-data':p=e/'handler-0/kernel-exit-events.json';d=json.loads(p.read_text());d[1]['data']=15
    elif fault=='order':d.reverse()
    elif fault=='event-status':d[1]['fflags']=2147483648
    elif fault=='report':p=e/'default-1/result.json';d=json.loads(p.read_text());d['record']['report']=None
    elif fault=='root-code':p=e/'default-1/result.json';d=json.loads(p.read_text());d['record']['report']['target_code']=0
    elif fault=='abort':p=e/'default-1/result.json';d=json.loads(p.read_text());d['record']['privateAbortRequested']=True
    elif fault=='peer':p=e/'handler-0/child.raw';p.write_bytes(b'wrong');d=None
    elif fault=='default-peer':p=e/'default-1/child.raw';p.write_bytes(b'wrong');d=None
    elif fault=='watcher-wait':p=e/'default-1/watcher-wait.json';d=json.loads(p.read_text());d['status']=1
    elif fault=='registered':p=e/'default-1/registered.json';d=json.loads(p.read_text());d['birth_rechecked']=False
    elif fault in ['reaped','aa']:p=e/'scope.json';d=json.loads(p.read_text());d['child_reaped_qualified' if fault=='reaped' else 'default_aa_qualified']=True
    elif fault=='startup-accept':p=e/'default-0/result.json';d=json.loads(p.read_text());d['error']=None
    elif fault=='startup-wait':p=e/'wait-default-0.json';d=json.loads(p.read_text());d['code']=0
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='runtime':p=e/'environment.json';d=json.loads(p.read_text());d['runtime_sha256']='0'*64
    else:p=e/'slots.json';d=json.loads(p.read_text());d['used']=5
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='fe2e2bc0faf45ca36750497c026e87f30ba110e201d149f36135519f9b1e8e6a'
