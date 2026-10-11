import base64
import pathlib
import plistlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.plistdecode import fixtures,assess


class PlistDecodeTests(unittest.TestCase):
    def record(self,raw,value):
        r={'input_base64':base64.b64encode(raw).decode(),'data_present':True,'data_base64':base64.b64encode(raw).decode(),
           'foundation_present':value is not None,'foundation_dictionary':isinstance(value,dict),'image':{'uuid':'owned'},'outcome':'returned','dictionary_type':isinstance(value,dict)}
        foundation=raw.decode('ascii') if raw in (b'bplist00',b'owned-invalid') else value
        r['foundation_present']=foundation is not None
        if foundation is not None:r['foundation_value_base64']=base64.b64encode(plistlib.dumps(foundation,fmt=plistlib.FMT_BINARY)).decode()
        if value is not None:r['value_base64']=base64.b64encode(plistlib.dumps(value,fmt=plistlib.FMT_BINARY)).decode()
        return r

    def test_fixtures_have_independent_decode_expectations(self):
        self.assertEqual(len(fixtures()),8)
        for name,raw,value in fixtures():
            if value is None:
                with self.assertRaises(Exception):plistlib.loads(raw)
            else:self.assertEqual(plistlib.loads(raw),value)
            self.assertTrue(assess(self.record(raw,value),raw,value)['passed'],name)

    def test_partial_exit_wrong_decode_and_type_substitution_reject(self):
        raw=plistlib.dumps({'owned':'value'},fmt=plistlib.FMT_BINARY);value={'owned':'value'}
        self.assertEqual(assess(self.record(raw,value),raw,value,1)['failure'],'helper-exit')
        for key,bad in [('foundation_present',1),('foundation_dictionary',1),('value_base64',base64.b64encode(plistlib.dumps({})).decode()),('input_base64','%%%')]:
            r=self.record(raw,value);r[key]=bad;self.assertFalse(assess(r,raw,value)['passed'])
        self.assertFalse(assess({},raw,value)['passed'])

    def test_invalid_native_outcome_is_observed_not_assumed(self):
        for outcome in ('returned','exception'):
            r=self.record(b'',None);r['outcome']=outcome
            self.assertTrue(assess(r,b'',None)['passed'])
        r=self.record(b'',None);r['data_base64']=base64.b64encode(b'changed').decode()
        self.assertFalse(assess(r,b'',None)['exact_data'])

if __name__=='__main__':unittest.main()
