import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('peer_reader',Path(__file__).with_name('verify_gpu_event_peer.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class PeerTests(unittest.TestCase):
 def test_separate_peer_signal_and_wrong_event(self):
  e=ROOT/'research/evidence/gpu-event-peer-2026-10-11';self.assertEqual((ROOT/'tools/re/gpu_event_peer.m').read_bytes(),(e/'gpu_event_peer.m').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],131072)
 def test_resealed_identity_exit_cleanup_completion_and_padding(self):
  for kind in ['wait','samepid','accepted','wrong','pending','completion','peerexit','cleanup','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-event-peer-2026-10-11',e);p=e/'result-0.json';d=json.loads(p.read_text());w=e/'wait-0.json';wd=json.loads(w.read_text())
    if kind=='wait':wd['parent_wait']=1
    elif kind=='samepid':d['peer_pid']=d['pid'];d['reply']['pid']=d['pid']
    elif kind=='accepted':d['reply']['accepted_parent']+=1
    elif kind=='wrong':d['value_after_rpc']=7;d['reply']['after']=7
    elif kind=='pending':d['rpc_pending_wait']=0
    elif kind=='completion':d['completion_status']=0
    elif kind=='peerexit':wd['last_exit_code']=2
    elif kind=='cleanup':wd['after_cleanup_print_wait']=0
    else:
     b=bytearray(base64.b64decode(d['after']));b[44 if kind=='padding' else 16383]^=1;d['after']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));w.write_text(json.dumps(wd));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
