import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cleanup_reader',Path(__file__).with_name('verify_compiler_qualification_cleanup.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerQualificationCleanupTests(unittest.TestCase):
 def test_seal_and_implementation(self):
  e=ROOT/'research/evidence/compiler-observer-qualification-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertFalse(reader.verify(e)['native_observer_qualified']);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'sourcecache-after-cleanup.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['qualified','cold','retry','root-exit','lost-original','lost-cleanup','actual-signal','marker','heartbeat','plain']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-observer-qualification-2026-10-11',e);p=e/'denied-control/result.json';d=json.loads(p.read_text())
    if fault in ['qualified','cold','retry']:
     q=e/'retained-failure.json';v=json.loads(q.read_text());v[{'qualified':'native_post_root_observer_qualified','cold':'cold_build_attempted','retry':'producer_retry'}[fault]]=True;q.write_text(json.dumps(v))
    elif fault=='root-exit':d['root_exit_code']=42
    elif fault=='lost-original':d['failure']['message']='Operation not permitted'
    elif fault=='lost-cleanup':d['failure']['cleanup_errors']=[]
    elif fault=='actual-signal':d['actual_signal_sent']=True
    elif fault=='plain':q=e/'plain.json';v=json.loads(q.read_text());v['code']=1;q.write_text(json.dumps(v))
    else:
     q=e/('denied-control/finished.bin' if fault=='marker' else 'detached/heartbeat.bin');b=bytearray(q.read_bytes());b[-1]^=1;q.write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
 def test_signal_failure_always_waits_and_preserves_original(self):
  from reloop.sourcecache import run_compiler
  for signal_error,wait_error in [(PermissionError('denied'),None),(PermissionError('denied'),subprocess.TimeoutExpired(['owned'],2)),(ProcessLookupError(),None)]:
   original=RuntimeError('observer failed');process=SimpleNamespace(pid=2147483647,poll=Mock(return_value=None),wait=Mock(return_value=0,side_effect=wait_error))
   def observer(roots,known):
    if roots:raise original
    return {}
   with patch('reloop.sourcecache.subprocess.Popen',return_value=process),patch('reloop.sourcecache.os.killpg',side_effect=signal_error):
    with self.assertRaises(RuntimeError) as raised:run_compiler(['owned'],observer=observer)
    self.assertIs(raised.exception,original);process.wait.assert_called_once_with(timeout=2)
    if isinstance(signal_error,PermissionError):self.assertTrue(original.compiler_cleanup_errors[0].startswith('group_signal:'))
    if wait_error:self.assertTrue(original.compiler_cleanup_errors[-1].startswith('root_wait:'))
 def test_reaped_root_is_not_signalled(self):
  from reloop.sourcecache import run_compiler
  original=RuntimeError('observer failed');process=SimpleNamespace(pid=2147483647,poll=Mock(side_effect=[None,0]),wait=Mock(return_value=0))
  def observer(roots,known):
   if roots:raise original
   return {}
  with patch('reloop.sourcecache.subprocess.Popen',return_value=process),patch('reloop.sourcecache.os.killpg') as signal:
   with self.assertRaises(RuntimeError):run_compiler(['owned'],observer=observer)
   signal.assert_not_called();process.wait.assert_called_once_with(timeout=2)

SEAL='aaa5bb70f9a8f2bcb0e6985207998c8c7e63e1f198ccc4e63ef2eb4fe86f6d80'
