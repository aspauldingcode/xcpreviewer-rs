"""Optimization must not disable native-evidence admission predicates."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

class OptimizedSendDestroyTests(unittest.TestCase):
    def test_existing_positive_and_all_faults_under_optimization(self):
        # Existing unittest assertions remain active under -O; they exercise the
        # full allocation, original/returned right distinction and rejected waits.
        script = """
import importlib.util, sys, unittest
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tools/re/tests'))
spec=importlib.util.spec_from_file_location('frozen_send_destroy_tests',root/'tools/re/tests/test_surface_send_destroy.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(module))
sys.exit(0 if result.wasSuccessful() else 1)
"""
        result = subprocess.run([sys.executable, '-O', '-c', script, str(ROOT)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
