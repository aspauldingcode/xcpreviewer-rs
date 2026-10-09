import pathlib
import sys
import unittest
import struct
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.continuation import inspect,inspect_default,inspect_cancel
from reloop.core import validate_experiment
import json

DEFAULT='''481c: 69 09 00 d0 adrp x9, 0x132000
4820: 00 00 00 00 ldr q0, [x9, #0x920]
4824: 00 00 00 00 str q0, [x8]
4828: 00 00 00 00 mov w9, #0x2
482c: 00 00 00 00 strb w9, [x8, #0x10]
4830: 00 00 00 00 ret
'''

class ConstantImage:
    def __init__(self,low,high):self.data=struct.pack('<QQ',low,high)
    def file_offset(self,address):
        if not 0x132920<=address<0x132930:raise ValueError('Unmapped constant')
        return address-0x132920

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

CANCEL='''100: 00 00 00 00 add x0, x22, #0x4c
104: 00 00 00 00 bl 0x900 ; symbol stub for: _os_unfair_lock_lock
108: 00 00 00 00 bl _$sFulfillOnceStatefulfill
10c: 00 00 00 00 add x0, x22, #0x4c
110: 00 00 00 00 bl 0x904 ; symbol stub for: _os_unfair_lock_unlock
114: 00 00 00 00 ldrb w8, [sp, #0xf]
118: 00 00 00 00 cmp w8, #0x1
11c: 00 00 00 00 b.ne 0x12c
120: 00 00 00 00 ldp x29, x30, [sp]
124: 00 00 00 00 add sp, sp, #0x80
128: 00 00 00 00 ret
12c: 00 00 00 00 ldp x0, x1, [x19, #0x10]
130: 00 00 00 00 ldr x2, [x1, #0x8]
144: 00 00 00 00 br x2
'''

class ContinuationTests(unittest.TestCase):
    def test_cancellation_first_fulfillment_dispatches_after_unlock(self):
        self.assertTrue(inspect_cancel(CANCEL)['cancel_action_after_unlock'])
        self.assertEqual(inspect_cancel(CANCEL)['cancel_skipped_outcome_tag'],1)

    def test_cancellation_boundary_mutations_fail(self):
        mutations=[CANCEL.replace('b.ne','b.eq'),CANCEL.replace('0x12c','0x130'),
                   CANCEL.replace('#0x4c','#0x50'),CANCEL.replace('#0xf','#0xe'),
                   CANCEL.replace('cmp w8, #0x1','cmp w8, #0x0'),
                   CANCEL.replace('ldr x2, [x1, #0x8]','ldr x2, [x1, #0x10]'),
                   CANCEL.replace('128: 00 00 00 00 ret','128: 00 00 00 00 nop'),
                   CANCEL+CANCEL.splitlines()[1]+'\n']
        for text in mutations:
            with self.assertRaises(ValueError):inspect_cancel(text)

    def test_static_controls_reject_nonboolean_parameters(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        experiments=json.loads((root/'research/loop/campaign.json').read_text())['experiments']
        for key in ['default_control','cancel_control']:
            e=next(e for e in experiments if key in e['params'])
            for value in [1,'true',None]:
                e['params'][key]=value
                with self.assertRaises(ValueError):validate_experiment(e)

    def test_default_constant_reads_complete_pair_and_static_predicates(self):
        for pair,branch in [((0,0),'logging'),((1,0),'assertion-helper'),((2,0),'fatal-call-and-trap'),((1,1),'fatal-call-and-trap')]:
            facts=inspect_default(DEFAULT,ConstantImage(*pair))
            self.assertEqual(facts['default_payload_words'],list(pair))
            self.assertEqual(facts['default_constant_bytes'],16)
            self.assertEqual(facts['default_static_branch'],branch)

    def test_default_changed_dataflow_and_truncated_constant_fail(self):
        for text in [DEFAULT.replace('#0x2','#0x3'),DEFAULT.replace('[x8]','[x7]'),DEFAULT.replace('x9, 0x132000','x10, 0x132000'),DEFAULT.replace('4830: 00 00 00 00 ret\n','')]:
            with self.assertRaises(ValueError):inspect_default(text,ConstantImage(1,0))
        image=ConstantImage(1,0);image.data=image.data[:-1]
        with self.assertRaises(ValueError):inspect_default(DEFAULT,image)

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
