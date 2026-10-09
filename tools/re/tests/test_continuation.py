import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.continuation import inspect

TEXT='''100: 00 00 00 00 add x0, x23, #0x4c
104: 00 00 00 00 bl 0x900 ; symbol stub for: _os_unfair_lock_lock
108: 00 00 00 00 bl _$sFulfillOnceStatefulfill
10c: 00 00 00 00 add x0, x23, #0x4c
110: 00 00 00 00 bl 0x904 ; symbol stub for: _os_unfair_lock_unlock
114: 00 00 00 00 ldrb w8, [sp]
118: 00 00 00 00 cmp w8, #0x1
11c: 00 00 00 00 b.eq 0x124
120: 00 00 00 00 blr x19
124: 00 00 00 00 ldp x29, x30, [sp]
128: 00 00 00 00 ret
'''

class ContinuationTests(unittest.TestCase):
    def test_observed_static_guard_excludes_callback_from_lock(self):
        self.assertTrue(inspect(TEXT)['callback_after_unlock'])
        self.assertEqual(inspect(TEXT)['skipped_outcome_tag'],1)

    def test_missing_duplicate_and_bypass_evidence_fail_closed(self):
        mutations=[TEXT.replace('bl 0x904 ; symbol stub for: _os_unfair_lock_unlock','mov x0, x1'),
                   TEXT+TEXT.splitlines()[1]+'\n',TEXT.replace('b.eq 0x124','b.ne 0x124'),
                   TEXT.replace('b.eq 0x124','b.eq 0x120'),TEXT.replace('cmp w8, #0x1','cmp w8, #0x0'),
                   TEXT.replace('add x0, x23, #0x4c','add x0, x23, #0x50'),
                   TEXT.replace('_os_unfair_lock_lock','_os_unfair_lock_unlock',1)]
        for text in mutations:
            with self.assertRaises(ValueError):inspect(text)

if __name__=='__main__':unittest.main()
