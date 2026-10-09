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

if __name__=='__main__':unittest.main()
