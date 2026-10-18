import unittest,math
from geometry import calibrate
class Tests(unittest.TestCase):
 def test_safe_point(self):self.assertEqual(calibrate([2800,1800],[2164,1028,2332,1076],[600,180,1520,1700])['raw_point'],[1124,526])
 def test_candidate_unsafe(self):
  with self.assertRaises(ValueError):calibrate([1400,900],[1082,514,1166,538],[600,180,1520,1700])
 def test_wrong_editor(self):
  with self.assertRaises(ValueError):calibrate([2800,1800],[2164,1028,2332,1076],[100,100,500,500])
 def test_invalid_types(self):
  for x in [True,float('nan'),float('inf'),'2800']:
   with self.assertRaises(ValueError):calibrate([x,1800],[2164,1028,2332,1076],[600,180,1520,1700])
 def test_border_reject(self):
  with self.assertRaises(ValueError):calibrate([2800,1800],[2164,1028,2800,1076],[600,180,1520,1700])
if __name__=='__main__':unittest.main()
