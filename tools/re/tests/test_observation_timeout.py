import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from reloop.core import execute
from reloop.processes import snapshot

class ObservationTimeoutTests(unittest.TestCase):
    def test_observation_timeout_is_retained_and_owned_child_reaped(self):
        calls=0;events=[]
        def bounded_snapshot(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==3:raise subprocess.TimeoutExpired(['/bin/ps','owned-test'],2)
            return snapshot(*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp,patch('reloop.processes.snapshot',side_effect=bounded_snapshot):
            root=pathlib.Path(tmp)
            result=execute([sys.executable,'-c','import time;time.sleep(30)'],root,5,1048576,lambda k,v:events.append((k,v)))
            self.assertEqual(result['execution'],'failed')
            self.assertIsNotNone(result['exit_code'])
            self.assertIn('TimeoutExpired', (root/'stderr.txt').read_text())
            self.assertTrue(any(k=='owned_descendant_cleanup' for k,_ in events))
            self.assertGreaterEqual(calls,6)
