import unittest
from sample_accounting import check
class Controls(unittest.TestCase):
 def test_independent_schedule(self):self.assertEqual(check([28,71,127,217])['count'],4)
 def test_partial(self):self.assertEqual(check([28,71,127])['count'],3)
 def test_cap(self):
  for h in [[],[28,71,127,217,307]]:
   with self.assertRaises(ValueError):check(h)
 def test_catchup(self):
  for h in [[28,45,90,180],[28,71,100,190],[28,71,127,180]]:
   with self.assertRaises(ValueError):check(h)
 def test_type_and_nonfinite(self):
  for x in [True,float('nan'),float('inf'),'217']:
   with self.assertRaises(ValueError):check([28,71,127,x])
if __name__=='__main__':unittest.main()
