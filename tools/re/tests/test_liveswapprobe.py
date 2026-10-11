import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'live-swap-probe.py'
spec = importlib.util.spec_from_file_location('owned_swap_probe', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SwapSupervisorTests(unittest.TestCase):
    def test_owned_session_timeout_prevents_late_child_write(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'late'
            code = 'import os,time,sys\nif os.fork()==0:\n time.sleep(0.6)\n open(sys.argv[1],"w").write("late")\nelse:\n time.sleep(10)\n'
            with open(os.devnull, 'wb') as output:
                with self.assertRaises(subprocess.TimeoutExpired):
                    module.execute_owned([sys.executable, '-c', code, str(target)],
                                         output, output, os.environ.copy(), 0.2)
            time.sleep(0.7)
            self.assertFalse(target.exists())
