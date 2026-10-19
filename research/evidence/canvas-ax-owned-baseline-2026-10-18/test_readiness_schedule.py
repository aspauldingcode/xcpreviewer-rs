import unittest
from readiness_schedule import decide
class ScheduleTests(unittest.TestCase):
 def test_fixed_spacing(self):
  history=[]
  for due in [15,45,90,180]:
   self.assertEqual(decide(0,due-1,240,300,history)['decision'],'independent_work')
   self.assertEqual(decide(0,due,240,300,history)['decision'],'sample_once');history.append(due)
  self.assertEqual(decide(0,181,240,300,history)['reason'],'observation cap')
 def test_expired_does_not_replenish(self):
  for history in [[],[15],[15,45,90,180]]:self.assertEqual(decide(0,240,240,300,history)['decision'],'cleanup')
 def test_unfit_next_sample(self):self.assertEqual(decide(0,91,170,230,[15,45,90])['decision'],'cleanup')
 def test_fast_samples_reject(self):
  for history in [[1],[15,16],[15,45,46],[15,45,90,91]]:
   with self.assertRaises(ValueError):decide(0,200,240,300,history)
 def test_future_duplicate_and_overcap(self):
  for history in [[250],[15,15],[15,45,90,180,181]]:
   with self.assertRaises(ValueError):decide(0,200,240,300,history)
 def test_late_sample_cannot_bunch_or_extend_stop(self):
  self.assertEqual(decide(0,200,240,300,[200])['decision'],'independent_work')
  self.assertEqual(decide(0,230,240,300,[200])['decision'],'sample_once')
  self.assertEqual(decide(0,230,240,300,[200,230])['decision'],'cleanup')
  with self.assertRaises(ValueError):decide(0,200,240,300,[200,200])
 def test_clock_and_reserve_faults(self):
  for args in [(0,-1,240,300,[]),(0,1,240,299,[]),(True,1,240,300,[]),(0,float('nan'),240,300,[]),(0,1,240,300,[True]),(0,1,240,300,())]:
   with self.assertRaises(ValueError):decide(*args)
if __name__=='__main__':unittest.main()
