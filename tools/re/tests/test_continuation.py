import pathlib
import sys
import unittest
import struct
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.continuation import inspect,inspect_default,inspect_cancel,inspect_deinit,inspect_state_metadata,inspect_callbacks,inspect_isolation,inspect_invalidation
from reloop.core import validate_experiment
import json
import copy

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

DEINIT='''2ba54: 00 00 00 00 mov x8, x24
2ba5c: 00 00 00 00 bl _$sSynchronousAccessProvidingpeek
2ba60: 00 00 00 00 mov x0, x24
2ba68: 00 00 00 00 bl 0x900 ; symbol stub for: _swift_getEnumCaseMultiPayload
2ba6c: 00 00 00 00 cmp w0, #0x1
2ba70: 00 00 00 00 b.ne 0x2ba88
2ba80: 00 00 00 00 blr x8
2ba84: 00 00 00 00 b 0x2bbf0
2bb5c: 00 00 00 00 bl _$sUnfulfilledMa
2bb84: 00 00 00 00 bl 0x904 ; symbol stub for: _swift_allocError
2bbd8: 00 00 00 00 bl _$sFulfillmentFailureModefail
2bc18: 00 00 00 00 bl 0x908 ; symbol stub for: _swift_release
2bc3c: 00 00 00 00 ret
'''

class ContinuationTests(unittest.TestCase):
    def test_callback_wrappers_reject_wrong_context_branch_and_duplicate_evidence(self):
        def body(entry,rows):
            return '\n'.join(f'{p:x}: 00 00 00 00 {op} {args}' for p,op,args in [(entry,'nop','')]+rows)+'\n'
        texts=[body(0x129770,[(0x129788,'stp','x1, x2, [x8]'),(0x12978c,'stp','x3, x4, [x8, #0x10]'),(0x1297e4,'str','wzr, [x0, #0x4c]'),(0x1297e8,'strb','wzr, [x0, #0x49]'),(0x129844,'str','x21, [x19, #0x20]')]),
               body(0x129858,[(0x129870,'stp','x1, x2, [x8]'),(0x1298c8,'str','wzr, [x0, #0x4c]'),(0x1298cc,'strb','wzr, [x0, #0x49]'),(0x129928,'str','x21, [x19, #0x10]')]),
               body(0x1299f4,[(0x129a04,'ldr','x21, [x20]'),(0x129a08,'ldp','x22, x19, [x20, #0x10]'),(0x129a0c,'cbz','x21, 0x129a4c'),(0x129a10,'ldr','x20, [x20, #0x8]'),(0x129a44,'mov','x20, x21'),(0x129a48,'bl','_$sverifyIsolated'),(0x129a4c,'mov','x20, x19'),(0x129a50,'blr','x22'),(0x129a60,'ret','')]),
               body(0x129a64,[(0x129a68,'nop',''),(0x129a6c,'nop',''),(0x129a70,'ldp','x8, x20, [x20]'),(0x129a74,'blr','x8'),(0x129a78,'nop',''),(0x129a7c,'nop',''),(0x129a80,'ret','')])]
        self.assertTrue(inspect_callbacks(texts)['isolated_optional_actor_check'])
        for old,new in [('cbz','cbnz'),('mov x20, x19','mov x20, x21'),('verifyIsolated','enqueue'),('blr x22','blr x19'),('ldp x8, x20','ldp x8, x19'),('#0x49','#0x39')]:
            with self.assertRaises(ValueError):inspect_callbacks([t.replace(old,new) for t in texts])
        for bad in [texts[:-1],texts+[texts[0]],texts[:2]+[texts[2]+texts[2].splitlines()[1]+'\n']+texts[3:]]:
            with self.assertRaises(ValueError):inspect_callbacks(bad)

    def test_isolation_helper_requires_exact_extent_and_precondition(self):
        text='\n'.join(f'{p:x}: 00 00 00 00 nop' for p in range(0x114e38,0x114e6c,4))+'\n'
        text=text.replace('114e58: 00 00 00 00 nop','114e58: 00 00 00 00 mov x1, sp').replace('114e5c: 00 00 00 00 nop','114e5c: 00 00 00 00 bl 0x12feb4 ; symbol stub for: preconditionIsolated').replace('114e68: 00 00 00 00 nop','114e68: 00 00 00 00 ret')
        self.assertTrue(inspect_isolation(text)['isolation_precondition_verified'])
        for bad in [text.replace('preconditionIsolated','enqueue'),text.replace('0x12feb4','0x12feb8'),text.replace('114e40: 00 00 00 00 nop','114e40: 00 00 00 00 b 0x114e68'),text.replace('ret','nop'),text+text.splitlines()[1]+'\n',text.split('\n',1)[1]]:
            with self.assertRaises(ValueError):inspect_isolation(bad)

    def test_invalidation_weak_gate_lock_order_and_state_skip_faults(self):
        def body(rows):return '\n'.join(f'{p:x}: '+struct.pack('<I',word).hex(' ')+f' {op} {args}' for p,op,args,word in rows)+'\n'
        texts=[]
        for entry,site in [(0x419cc,0x419e4),(0x41f10,0x41f28)]:
            texts.append(body([(entry,'nop','',0),(site,'b','shared',0x14000000|((0x41f2c-site)//4))]))
        shared=[(0x41f2c,'nop',''),(0x41f70,'bl','0x13166c'),(0x41f74,'cbz','x0, 0x41fc4'),(0x41f88,'add','x0, x23, #0x54'),(0x41f8c,'bl','0x131120'),(0x41fa4,'blr','x20'),(0x41fa8,'add','x0, x23, #0x54'),(0x41fac,'bl','0x13112c'),(0x41fb0,'mov','x0, x22'),(0x41fb4,'bl','0x131498'),(0x41fc0,'blr','x19')]
        update=[(0xbeef0,'nop',''),(0xbef20,'ldrh','w8, [x0, #0x40]'),(0xbef3c,'ubfx','w8, w8, #8, #8'),(0xbef40,'cmp','w8, #0x1'),(0xbef44,'b.ne','0xbef68 <owned>'),(0xbef60,'mov','w8, #0x1'),(0xbef64,'b','0xbefec <owned>'),(0xbefd0,'blr','x23'),(0xbefd4,'mov','w8, #0x0'),(0xbefe8,'strb','wzr, [x27, #0x41]'),(0xbefec,'strb','w8, [x22, #0x8]')]
        texts += [body([(p,op,args,0) for p,op,args in rows]) for rows in [shared,update]]
        self.assertTrue(inspect_invalidation(texts)['cleanup_after_unlock'])
        for old,new in [('cbz','cbnz'),('#0x54','#0x50'),('0x13112c','0x131120'),('b.ne','b.eq'),('0xbefec','0xbefd0'),('mov w8, #0x0','mov w8, #0x1'),('#0x41','#0x40')]:
            with self.assertRaises(ValueError):inspect_invalidation([t.replace(old,new) for t in texts])
        bad=texts.copy();bad[0]=bad[0].replace('52 01 00 14','53 01 00 14')
        with self.assertRaises(ValueError):inspect_invalidation(bad)
        with self.assertRaises(ValueError):inspect_invalidation(texts[:-1])
        with self.assertRaises(ValueError):inspect_invalidation(texts+[texts[0]])

    def test_deinit_case_skip_and_diagnostic_require_observed_boundaries(self):
        self.assertEqual(inspect_deinit(DEINIT)['deinit_skipped_case'],1)
        for text in [DEINIT.replace('b.ne','b.eq'),DEINIT.replace('cmp w0, #0x1','cmp w0, #0x0'),DEINIT.replace('b 0x2bbf0','b 0x2bbd8'),DEINIT.replace('_swift_allocError','_swift_allocObject'),DEINIT.replace('FulfillmentFailureModefail','OtherFailureModefail'),DEINIT.replace('peek','update'),DEINIT.replace('2bc3c: 00 00 00 00 ret','')]:
            with self.assertRaises(ValueError):inspect_deinit(text)

    def test_metadata_case_names_are_not_assigned_runtime_tags(self):
        state={'name':'State','kind':18,'field_count':2,'address':'0x100','parent':{'name':'FulfillOnceState'},'fields':[{'name':'waiting'},{'name':'fulfilled','mangled_type':{'unresolved_symbolic_prefix_base64':'AA=='}}]}
        self.assertEqual(inspect_state_metadata({'types':[state]})['state_case_names'],['waiting','fulfilled'])
        for value in [{'types':[]},{'types':[state,state]}]:
            with self.assertRaises(ValueError):inspect_state_metadata(value)
        for key,value in [('kind',17),('field_count',1),('parent',{}),('fields',[{'name':'fulfilled'},{'name':'waiting'}])]:
            changed=copy.deepcopy(state);changed[key]=value
            with self.assertRaises(ValueError):inspect_state_metadata({'types':[changed]})

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
        for key in ['default_control','cancel_control','deinit_control','state_control','callback_control','isolation_control','invalidation_control']:
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
