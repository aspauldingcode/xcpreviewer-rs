import base64
import copy
import unittest
from reloop.browseralpha import inspect
from reloop.portablealpha import expected, CASES


class BrowserAlphaTests(unittest.TestCase):
    def fixture(self):
        jobs=[];rows=[]
        for n in range(9):
            for bg in (0,1):
                raw=expected(17,9,80,n,bg);active=b''.join(raw[y*80:y*80+68] for y in range(9));index=len(jobs)
                jobs.append({'index':index,'n':n,'bg':bg,'expected':raw,'native':active if (n,bg) in CASES else None})
                encoded=base64.b64encode(raw).decode()
                invalid=[{'args':args,'result':0,'allocation':encoded} for args in [[17,9,67,n,bg],[17,9,257,n,bg],[17,9,80,9,bg],[17,9,80,n,2]]]
                rows.append({'index':index,'n':n,'bg':bg,'capacity':16384,'rendered':720,'allocation':encoded,'invalid':invalid,'canvas':base64.b64encode(active).decode(),'context':{'alpha':True,'colorSpace':'srgb'},'image_color_space':'srgb'})
        return jobs,{'nonce':'owned','repeat':0,'origin':'http://127.0.0.1:42','module_sha256':'hash','imports':0,'user_agent':'unit fixture; not actual browser evidence','rows':rows}

    def check(self,report,jobs):
        return inspect(report,jobs,'owned',0,'http://127.0.0.1:42','hash')

    def test_full_counts(self):
        jobs,report=self.fixture();result=self.check(report,jobs)
        self.assertEqual(result['allocation_bytes'],294912)
        self.assertEqual(result['invalid_bytes'],1179648)
        self.assertEqual(result['canvas_bytes'],11016)
        self.assertEqual(result['native_bytes'],4896)

    def test_pixel_padding_tail_and_invalid_mutations(self):
        jobs,report=self.fixture()
        for offset in (0,3,68,720,16383):
            changed=copy.deepcopy(report);raw=bytearray(jobs[0]['expected']);raw[offset]^=1
            changed['rows'][0]['allocation']=base64.b64encode(raw).decode()
            with self.assertRaises(ValueError):self.check(changed,jobs)
        changed=copy.deepcopy(report);changed['rows'][0]['invalid'][0]['allocation']=base64.b64encode(b'wrong').decode()
        with self.assertRaises(ValueError):self.check(changed,jobs)
        changed=copy.deepcopy(report);changed['rows'][0]['canvas']=base64.b64encode(b'\xff'*612).decode()
        with self.assertRaises(ValueError):self.check(changed,jobs)

    def test_identity_repeats_context_and_bool_metadata(self):
        jobs,report=self.fixture()
        for key,value in [('nonce','stale'),('repeat',True),('origin','http://127.0.0.1:43'),('module_sha256','other'),('imports',False)]:
            changed=copy.deepcopy(report);changed[key]=value
            with self.assertRaises(ValueError):self.check(changed,jobs)
        for key,value in [('index',False),('context',{'alpha':False,'colorSpace':'srgb'}),('image_color_space','display-p3')]:
            changed=copy.deepcopy(report);changed['rows'][0][key]=value
            with self.assertRaises(ValueError):self.check(changed,jobs)
