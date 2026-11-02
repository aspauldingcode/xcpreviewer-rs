import json
import subprocess
import unittest
from unittest.mock import patch
from reloop.libprocobserver import Observer
from reloop.processes import OwnedTree

class LibprocObserverTests(unittest.TestCase):
    def result(self,rows):return subprocess.CompletedProcess([],0,json.dumps(rows).encode(),b'')
    def row(self,identity=(100,123,'/owned')):
        return {'pid':101,'parent':1,'group':101,'state':'L','identity':list(identity)}
    def test_bounded_known_lifetime_arguments_and_tuple_identity(self):
        with patch('reloop.libprocobserver.subprocess.run',return_value=self.result([self.row()])) as run:
            rows=Observer('/helper').snapshot({101},{101:(100,123,'/owned')})
        self.assertEqual(run.call_args.args[0],['/helper','101','101:100:123'])
        self.assertEqual(run.call_args.kwargs['timeout'],2)
        self.assertEqual(rows[101]['identity'],(100,123,'/owned'))
    def test_reject_duplicate_invalid_or_relative_identity(self):
        for rows in ([self.row(),self.row()],[self.row((True,1,'/owned'))],[self.row((1,2,'relative'))]):
            with patch('reloop.libprocobserver.subprocess.run',return_value=self.result(rows)):
                with self.assertRaises(ValueError):Observer('/helper').snapshot(set())
    def test_timeout_and_nonzero_propagate_fail_closed(self):
        for error in (subprocess.TimeoutExpired('/helper',2),subprocess.CalledProcessError(2,'/helper')):
            with patch('reloop.libprocobserver.subprocess.run',side_effect=error):
                with self.assertRaises(type(error)):Observer('/helper').snapshot({100})
    def test_changed_birth_or_executable_never_signalled(self):
        for actual in ((101,123,'/owned'),(100,124,'/owned'),(100,123,'/replacement')):
            tree=OwnedTree(100);tree.known={101:(100,123,'/owned')}
            rows={101:{'parent':1,'group':101,'state':'L','identity':actual}}
            with patch('reloop.processes.snapshot',return_value=rows),patch('reloop.processes.os.kill') as kill:
                tree.drain();kill.assert_not_called()

    def test_unicode_executable_bytes_round_trip(self):
        path='/owned/雪';wire=path.encode('utf8').decode('latin1')
        with patch('reloop.libprocobserver.subprocess.run',return_value=self.result([self.row((100,123,wire))])):
            self.assertEqual(Observer('/helper').snapshot({101})[101]['identity'][2],path)

    def test_missing_live_root_is_not_successful_absence(self):
        with patch('reloop.libprocobserver.subprocess.run',return_value=self.result([])),patch('reloop.libprocobserver.os.kill'):
            with self.assertRaises(OSError):Observer('/helper').snapshot({100})
        with patch('reloop.libprocobserver.subprocess.run',return_value=self.result([])),patch('reloop.libprocobserver.os.kill',side_effect=ProcessLookupError):
            self.assertEqual(Observer('/helper').snapshot({100}),{})
    def test_invalid_roots_rejected_before_native_execution(self):
        for roots in ({True},{0},{-1},{2147483648}):
            with patch('reloop.libprocobserver.subprocess.run') as run:
                with self.assertRaises(ValueError):Observer('/helper').snapshot(roots)
                run.assert_not_called()

    def test_executor_retains_prelaunch_observation_failures(self):
        import tempfile
        from pathlib import Path
        from reloop.core import execute
        for error in (subprocess.CalledProcessError(6,'/helper'),ValueError('Invalid snapshot')):
            with tempfile.TemporaryDirectory() as tmp:
                def unavailable(*args,**kwargs):raise error
                with patch('reloop.core.subprocess.Popen') as launch:
                    result=execute(['/owned'],Path(tmp),2,4096,observer=unavailable)
                launch.assert_not_called()
                self.assertEqual(result['execution'],'failed')
                self.assertIsNone(result['exit_code'])
                self.assertIn(type(error).__name__,(Path(tmp)/'stderr.txt').read_text())
