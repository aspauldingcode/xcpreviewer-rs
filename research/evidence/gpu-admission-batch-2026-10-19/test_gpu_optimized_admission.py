"""Keep the existing grouped GPU admission faults active under optimization."""
import ast,subprocess,sys,unittest
from pathlib import Path
NAMES=['gpu_buffer_owner','gpu_buffer_release','gpu_event_carrier','gpu_event_disconnect','gpu_event_failure','gpu_event_peer','gpu_queue_order','gpu_submission_lifetime']
class GpuOptimizedAdmissionTests(unittest.TestCase):
 def test_admission_checks_are_not_assert_statements(self):
  for name in NAMES:
   with self.subTest(reader=name):
    tree=ast.parse(Path(__file__).with_name('verify_'+name+'.py').read_text())
    self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(tree)))
 @unittest.skipIf(not __debug__,'Already running optimized existing controls separately')
 def test_existing_fault_controls_under_optimization(self):
  z=subprocess.run([sys.executable,'-O','-B','-m','unittest',*['test_'+n for n in NAMES]],cwd=Path(__file__).parent,capture_output=True,text=True,timeout=30)
  self.assertEqual(z.returncode,0,z.stdout+z.stderr)
  self.assertIn('Ran 16 tests',z.stderr)
if __name__=='__main__':unittest.main()
