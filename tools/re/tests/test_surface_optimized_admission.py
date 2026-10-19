"""Keep the existing grouped CPU surface admission faults active under optimization."""
import ast,subprocess,sys,unittest
from pathlib import Path
NAMES=['remote_surface_alias', 'remote_surface_seed', 'remote_surface_use', 'surface_alias_use', 'surface_content_seed', 'surface_global_id', 'surface_invalid_destroy', 'surface_queued_drop', 'surface_rejected_envelope', 'surface_seed_timing', 'surface_send_retry', 'surface_send_timeout', 'surface_stream_close', 'surface_use_count']
class SurfaceOptimizedAdmissionTests(unittest.TestCase):
 def test_admission_checks_are_not_assert_statements(self):
  for name in NAMES:
   with self.subTest(reader=name):
    tree=ast.parse(Path(__file__).with_name('verify_'+name+'.py').read_text())
    self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(tree)))
 @unittest.skipIf(not __debug__,'Already running optimized existing controls separately')
 def test_existing_fault_controls_under_optimization(self):
  z=subprocess.run([sys.executable,'-O','-B','-m','unittest',*['test_'+n for n in NAMES]],cwd=Path(__file__).parent,capture_output=True,text=True,timeout=30)
  self.assertEqual(z.returncode,0,z.stdout+z.stderr)
  self.assertIn('Ran 28 tests',z.stderr)
if __name__=='__main__':unittest.main()
