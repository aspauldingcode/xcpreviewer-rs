import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('queued_reader',Path(__file__).with_name('verify_surface_queued_drop.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class QueuedDropTests(unittest.TestCase):
 def test_owned_queued_drop_accounting(self):
  e=ROOT/'research/evidence/surface-queued-drop-2026-10-11'
  for n in ['surface_queued_drop.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re'/n).read_bytes(),(e/n).read_bytes())
  self.assertEqual(reader.verify(e)['complete_bytes'],196608)
 def test_resealed_queue_rights_completion_peer_exit_padding_tail(self):
  for kind in ['queue','rights','completion','peer','exit','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-queued-drop-2026-10-11',e);f=e/'move-0';p=f/'result.json';d=json.loads(p.read_text())
    if kind=='queue':d['queued_messages_before_drop']=0
    elif kind=='rights':d['sender_refs_after_send']=1
    elif kind=='completion':d['completion_accepted']=True
    elif kind=='peer':d['receiver_pid']=d['sender_pid']
    elif kind=='exit':(f/'wait.json').write_text(json.dumps({'code':1,'timeout':False,'stderr':''}))
    else:
     b=bytearray((f/'port-only.bin').read_bytes());b[44 if kind=='padding' else 16383]^=1;(f/'port-only.bin').write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
