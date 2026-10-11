import tempfile
import sys
import time
import unittest
from pathlib import Path
from reloop.core import execute


class OwnedProcessTests(unittest.TestCase):
    def test_detached_descendant_cannot_write_after_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            child = "import os,time,pathlib;os.setsid();time.sleep(1.8);pathlib.Path(%r).write_text('late')" % str(out/'late')
            parent = "import subprocess,time,sys;subprocess.Popen([sys.executable,'-c',%r]);time.sleep(30)" % child
            result = execute([sys.executable, '-c', parent], out, 0.7, 1024*1024)
            self.assertEqual(result['execution'], 'timed_out')
            time.sleep(1.5)
            self.assertFalse((out/'late').exists())

    def test_reused_identity_is_excluded(self):
        from unittest.mock import patch
        from reloop.processes import OwnedTree
        tree = OwnedTree(100)
        tree.known = {101: ('original',)}
        with patch('reloop.processes.snapshot', return_value={101: {'parent':1,'group':101,'identity':('different',)}}), patch('reloop.processes.os.kill') as kill:
            tree.drain()
            kill.assert_not_called()

    def test_live_owned_root_exec_still_discovers_children(self):
        from unittest.mock import Mock, patch
        from reloop.processes import OwnedTree
        process=Mock();process.poll.return_value=None
        tree=OwnedTree(100,process);tree.known={100:('old executable',)}
        rows={100:{'parent':1,'group':100,'identity':('new executable',)},
              101:{'parent':100,'group':101,'identity':('detached child',)}}
        with patch('reloop.processes.snapshot',return_value=rows):
            tree.observe()
        self.assertEqual(tree.known[101],('detached child',))
