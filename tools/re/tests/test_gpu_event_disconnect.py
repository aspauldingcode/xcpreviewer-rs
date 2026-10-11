import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('disconnect_reader',Path(__file__).with_name('verify_gpu_event_disconnect.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class DisconnectTests(unittest.TestCase):
 def test_retained_and_dropped_peer_event_after_disconnect(self):
  e=ROOT/'research/evidence/gpu-event-disconnect-2026-10-11';self.assertEqual((ROOT/'tools/re/gpu_event_disconnect.m').read_bytes(),(e/'gpu_event_disconnect.m').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],131072)
 def test_resealed_owner_identity_token_order_exit_cleanup_bytes(self):
  for kind in ['wait','owners','peer','token','drop','pending','completion','peerexit','cleanup','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-event-disconnect-2026-10-11',e);p=e/'drop/result-0.json';d=json.loads(p.read_text());w=e/'drop/wait-0.json';wd=json.loads(w.read_text())
    if kind=='wait':wd['parent_wait']=1
    elif kind=='owners':d['original_owners_cleared']=False
    elif kind=='peer':d['second_pid']+=1
    elif kind=='token':d['second_reply']['before_token']+=1
    elif kind=='drop':d['after_second']=7
    elif kind=='pending':d['disconnected_wait']=0
    elif kind=='completion':d['completion_status']=0
    elif kind=='peerexit':wd['last_exit_code']=47
    elif kind=='cleanup':wd['after_cleanup_print_wait']=0
    else:
     b=bytearray(base64.b64decode(d['after']));b[44 if kind=='padding' else 16383]^=1;d['after']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));w.write_text(json.dumps(wd));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
