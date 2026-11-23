"""Owned subprocess controls, not native SwiftUI or real Cargo tests."""
import sys
import time
import unittest
from startup import run_decoder_build


class Tests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(run_decoder_build([sys.executable, '-c', 'print("built")']), b'built\n')

    def test_failure_preserves_diagnostic(self):
        with self.assertRaisesRegex(RuntimeError, 'exit 7.*') as error:
            run_decoder_build([sys.executable, '-c', 'print("missing target");exit(7)'])
        self.assertIn('missing target', str(error.exception))

    def test_timeout_closes_descendant_output_pipe(self):
        # Child inherits stdout: communicate cannot return until it too closes.
        program = ('import subprocess,sys,time;'
                   'subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);'
                   'print("waiting for owned child",flush=True);time.sleep(30)')
        start = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, 'owned build group stopped') as error:
            run_decoder_build([sys.executable, '-c', program], timeout=.5)
        self.assertIn('waiting for owned child', str(error.exception))
        self.assertLess(time.monotonic() - start, 4)


if __name__ == '__main__':
    unittest.main()
