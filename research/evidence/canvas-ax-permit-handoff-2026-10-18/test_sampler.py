import unittest
from sampler import Sampler
class Tests(unittest.TestCase):
 def new(self):return Sampler(1000,10,1240,1300)
 def test_four_permits_with_completion_gaps(self):
  s=self.new()
  for ordinal,t in enumerate([15,46,92,183],1):
   self.assertEqual(s.issue(1000+t,10+t)['ordinal'],ordinal);s.complete(ordinal,'busy',1001+t,11+t)
  self.assertEqual(s.issue(1185,195)['decision'],'cleanup')
 def test_pending_and_replay(self):
  s=self.new();s.issue(1015,25)
  with self.assertRaises(ValueError):s.issue(1016,26)
  with self.assertRaises(ValueError):s.complete(True,'ready',1016,26)
  s.complete(1,'ready',1016,26)
  with self.assertRaises(ValueError):s.complete(1,'ready',1017,27)
 def test_late_first_cannot_bunch(self):
  s=self.new();s.issue(1180,190);s.complete(1,'busy',1181,191)
  self.assertEqual(s.issue(1181,191)['decision'],'independent_work')
  self.assertEqual(s.issue(1211,221)['ordinal'],2);s.complete(2,'busy',1212,222)
  self.assertEqual(s.issue(1212,222)['decision'],'cleanup')
 def test_error_never_replenishes(self):
  s=self.new();s.issue(1015,25);s.complete(1,'error',1016,26)
  self.assertEqual(s.issue(1046,56)['reason'],'recorded error')
 def test_clock_faults(self):
  for wall,mono in [(1000,9),(1020,11),(True,25),(1015,float('nan'))]:
   with self.assertRaises(ValueError):self.new().issue(wall,mono)
 def test_snapshot_cannot_reset_history(self):
  s=self.new();s.issue(1015,25);s.complete(1,'busy',1016,26);v=s.snapshot();v['history'].clear();v['records'].clear()
  self.assertEqual(s.issue(1017,27)['decision'],'independent_work');self.assertEqual(len(s.snapshot()['history']),1)
 def test_cutoff_and_late_completion(self):
  s=self.new();self.assertEqual(s.issue(1240,250)['decision'],'cleanup')
  s=self.new();s.issue(1239,249)
  with self.assertRaises(ValueError):s.complete(1,'busy',1240,250)
if __name__=='__main__':unittest.main()
