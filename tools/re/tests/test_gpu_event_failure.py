import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('failure_reader',Path(__file__).with_name('verify_gpu_event_failure.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class FailureTests(unittest.TestCase):
 def test_expected_peer_failures_and_fallback(self):
  e=ROOT/'research/evidence/gpu-event-failure-2026-10-11';self.assertEqual((ROOT/'tools/re/gpu_event_failure.m').read_bytes(),(e/'gpu_event_failure.m').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],131072)
 def test_resealed_failure_identity_order_exit_cleanup_bytes(self):
  for kind in ['wait','reply','error','identity','before_signal','pending','completion','peerexit','cleanup','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-event-failure-2026-10-11',e);p=e/'before/result-0.json';d=json.loads(p.read_text());w=e/'before/wait-0.json';wd=json.loads(w.read_text())
    if kind=='wait':wd['parent_wait']=1
    elif kind=='reply':d['reply']={}
    elif kind=='error':d['rpc_error_code']=0
    elif kind=='identity':j=json.loads(wd['peer_stdout']);j['accepted_parent']+=1;wd['peer_stdout']=json.dumps(j)
    elif kind=='before_signal':d['value_after_rpc']=7
    elif kind=='pending':d['rpc_pending_wait']=0
    elif kind=='completion':d['completion_status']=0
    elif kind=='peerexit':wd['last_exit_code']=0
    elif kind=='cleanup':wd['after_cleanup_print_wait']=0
    else:
     b=bytearray(base64.b64decode(d['after']));b[44 if kind=='padding' else 16383]^=1;d['after']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));w.write_text(json.dumps(wd));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
