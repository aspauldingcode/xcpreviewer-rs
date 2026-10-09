import copy
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacepayload import EXPECTED,select,has_ancestor
from reloop.discriminants import interpret


def metadata():
    fields=[{'name':n} for n in EXPECTED]
    return {'types':[{'name':'IOSurfacePayload','kind':17,'fields':fields},
                     {'name':'Key','kind':18,'fields':copy.deepcopy(fields),'parent':{'name':None,'parent':{'name':'IOSurfacePayload'}}},
                     {'name':'Key','kind':18,'fields':[{'name':'unrelated'}],'parent':{'name':'OtherPayload'}}]}


class SurfacePayloadTests(unittest.TestCase):
    def test_nested_key_selection_excludes_unrelated_enum(self):
        payload,key,names=select(metadata());self.assertEqual(names,list(EXPECTED))
        self.assertTrue(has_ancestor(key,'IOSurfacePayload'))
        cycle={};cycle['parent']=cycle
        self.assertFalse(has_ancestor(cycle,'IOSurfacePayload'))

    def test_conditional_select_respects_comparison_width_and_signed_overflow(self):
        def code(register, immediate):
            ops=[('ldrb','w8, [x20]'),('mov','x9, #0xe100000000000000'),
                 ('mov','x10, #0x52'),('mov','x11, #0x4c'),
                 ('mov','x12, #0x8000000000000000'),('cmp',register+', #'+immediate),
                 ('csel','x0, x10, x11, gt'),('mov','x1, x9'),('ret','')]
            return {i*4:(op,args,0) for i,(op,args) in enumerate(ops)}
        for selector,name in [(0,'L'),(1,'L'),(2,'R')]:
            self.assertEqual(interpret(None,code('w8','1'),selector)['raw_value'],name)
        self.assertEqual(interpret(None,code('w8','0xffffffff'),0)['raw_value'],'R')
        self.assertEqual(interpret(None,code('x12','1'),0)['raw_value'],'L')

    def test_conditional_select_without_flags_or_unknown_condition_rejects(self):
        for condition in ('eq','unsupported'):
            code={0:('ldrb','w8, [x20]',0),4:('csel','x0, x8, x8, '+condition,0)}
            with self.assertRaises(ValueError):interpret(None,code,0)

    def test_ambiguous_changed_or_missing_contract_fails_closed(self):
        for mutation in ('duplicate','missing','reordered','changed'):
            data=metadata()
            if mutation=='duplicate':data['types'].append(copy.deepcopy(data['types'][1]))
            elif mutation=='missing':data['types'].pop(0)
            elif mutation=='reordered':data['types'][1]['fields'].reverse()
            else:data['types'][0]['fields'][0]['name']='generation'
            with self.assertRaises(ValueError):select(data)


class CodecBoundaryTests(unittest.TestCase):
    def test_fields_and_key_cases_remain_separate(self):
        from reloop.surfacepayload import CONTRACTS
        for control in ('BitmapDescription','ServiceMessage','ServiceMessagePayload'):
            typename,keyname,fields,cases,_=CONTRACTS[control]
            data={'types':[{'name':typename,'kind':17,'fields':[{'name':n} for n in fields]},
                           {'name':keyname,'kind':18,'fields':[{'name':n} for n in cases],'parent':{'name':typename}}]}
            self.assertEqual(select(data,control)[2],list(cases))
            self.assertNotEqual(fields,cases)

    def test_register_input_mask_and_signed_branch(self):
        ops=[('and','w8, w0, #0xff'),('cmp','w8, #3'),('b.le','0x1c'),
             ('mov','x0, #0x52'),('mov','x1, #0xe100000000000000'),('ret',''),
             ('b','0x18'),('mov','x0, #0x4c'),('mov','x1, #0xe100000000000000'),('ret','')]
        code={i*4:(op,args,0) for i,(op,args) in enumerate(ops)}
        for selector,expected in ((0,'L'),(3,'L'),(4,'R'),(8,'R')):
            self.assertEqual(interpret(None,code,selector,entry='w0')['raw_value'],expected)
        with self.assertRaises(ValueError):interpret(None,code,0)
        with self.assertRaises(ValueError):interpret(None,code,0,entry='constant')

    def test_constant_literal_and_branch_fail_closed(self):
        code={0:('mov','x0, #0x41',0),4:('mov','x1, #0xe100000000000000',0),8:('ret','',0)}
        self.assertEqual(interpret(None,code,0,entry='constant')['raw_value'],'A')
        for bad in ({0:('b.le','0x4',0)}, {0:('cmp','w0, #1',0),4:('b.le','0x100',0)},
                    {0:('cmp','w0, #1',0),4:('b.ne','0x100',0)}):
            with self.assertRaises(ValueError):interpret(None,bad,0,entry='w0')
        with self.assertRaises(ValueError):interpret(None,code,0,entry='unknown')

if __name__=='__main__':unittest.main()
