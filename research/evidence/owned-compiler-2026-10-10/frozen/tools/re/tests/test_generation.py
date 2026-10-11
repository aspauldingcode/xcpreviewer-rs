import unittest
from reloop.generation import Gate,Ticket,controls

class GenerationTests(unittest.TestCase):
    def test_independent_table_mutable_vs_separate(self):
        for mode,delayed in [('reuse',b'b'),('separate',b'a')]:self.assertTrue(controls(b'a',b'b',delayed,mode)['passed'])
        self.assertFalse(controls(b'a',b'b',b'a','reuse')['passed'])
    def test_failed_commit_preserves_last_frame_and_pending(self):
        g=Gate();a=g.admit(1,b'a');self.assertTrue(g.commit(a,b'a'));b=g.admit(2,b'b');self.assertFalse(g.commit(b,b'wrong'));self.assertEqual(g.frame,b'a');self.assertTrue(g.commit(b,b'b'))
    def test_reset_does_not_reuse_ticket_and_duplicate_cannot_commit(self):
        g=Gate();a=g.admit(1,b'a');g.reset();b=g.admit(1,b'a');self.assertNotEqual(a,b);self.assertFalse(g.commit(a,b'a'));self.assertTrue(g.commit(b,b'a'));self.assertFalse(g.commit(b,b'a'))
    def test_invalid_generations_and_payloads(self):
        for value in (True,0,-1,2**64,'1'):
            with self.assertRaises(ValueError):Gate().admit(value,b'a')
        for value in (b'',bytearray(b'a'),b'a'*1048577):
            with self.assertRaises(ValueError):Gate().admit(1,value)
        g=Gate();g.admit(2,b'a')
        with self.assertRaises(ValueError):g.admit(1,b'a')
        self.assertFalse(g.commit(Ticket(99,2,1),b'a'))
