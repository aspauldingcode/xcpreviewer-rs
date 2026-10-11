import base64,copy,json,pathlib,tempfile,unittest
from reloop.browserwasm import inspect,CAPACITY
from reloop.core import source_files

class BrowserWasmTests(unittest.TestCase):
    def fixture(self,root):
        jobs=[];rows=[]
        for i in range(4):
            raw=(b'\xff\x00\x00\xff' if i<3 else b'\x00\x00\xff\xff')+b'\xcd'*4
            (root/('pixels-%d.rgba'%i)).write_bytes(raw);full=raw+bytes([0xa5])*(CAPACITY-8);enc=base64.b64encode(full).decode()
            jobs.append(dict(index=i,stride=8,config=dict(width=1,height=1),module_sha256='m%d'%i))
            rows.append(dict(index=i,module_sha256='m%d'%i,imports=0,capacity=CAPACITY,rendered=8,allocation=enc,canvas=base64.b64encode(raw[:4]).decode(),invalid=[dict(stride=v,result=0,allocation=enc) for v in (0,3,1281,0xffffffff)]))
        return jobs,dict(nonce='n',repeat=0,user_agent='actual test fixture',origin='http://127.0.0.1:1234',rows=rows)
    def test_positive_and_allocation_padding_tail_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);jobs,r=self.fixture(p);self.assertEqual(inspect(r,jobs,'n',0,p)['allocation_bytes'],819200)
            for offset in (0,7,CAPACITY-1):
                bad=copy.deepcopy(r);raw=bytearray(base64.b64decode(bad['rows'][0]['allocation']));raw[offset]^=1;bad['rows'][0]['allocation']=base64.b64encode(raw).decode()
                with self.assertRaises(ValueError):inspect(bad,jobs,'n',0,p)
    def test_stale_identity_imports_canvas_and_intermediate_invalid_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);jobs,r=self.fixture(p)
            for field,value in (('nonce','old'),('repeat',True),('origin','https://remote')):
                bad=copy.deepcopy(r);bad[field]=value
                with self.assertRaises(ValueError):inspect(bad,jobs,'n',0,p)
            for field,value in (('imports',1),('module_sha256','wrong'),('capacity',True),('canvas',base64.b64encode(b'bad!').decode())):
                bad=copy.deepcopy(r);bad['rows'][0][field]=value
                with self.assertRaises(ValueError):inspect(bad,jobs,'n',0,p)
            bad=copy.deepcopy(r);bad['rows'][0]['invalid'][0]['allocation']=base64.b64encode(b'bad').decode()
            with self.assertRaises(ValueError):inspect(bad,jobs,'n',0,p)
    def test_browser_template_is_frozen_source(self):
        self.assertTrue(any(p.name=='browser_source.html' for p in source_files()))
    def test_browser_mode_rejects_ignored_source_flags(self):
        from reloop.core import validate_experiment
        q=json.loads(pathlib.Path('research/loop/campaign.json').read_text());e=copy.deepcopy(next(e for e in q['experiments'] if e['id']=='portable-browser-execution-repeat'))
        validate_experiment(e)
        for key,value in (('browser_control',1),('source_control',True),('second_runtime',True)):
            bad=copy.deepcopy(e);bad['params'][key]=value
            with self.assertRaises(ValueError):validate_experiment(bad)
