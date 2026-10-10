import base64
import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from reloop.browsersource import inspect,straight
from reloop.primarysource import expression,parse,expected
from reloop.core import load,ROOT,validate_experiment

class BrowserSourceTests(unittest.TestCase):
    def fixture(self,source):
        jobs=[];checkers=[];rows=[];invalid=[];controls=[];aggregates=[];negative=[]
        encode=lambda raw:base64.b64encode(raw).decode()
        for i in range(16):
            cfg=parse(expression(4,0,1 if i==14 else 64 if i==15 else 17,1 if i==14 else 64 if i==15 else 9));strides=[cfg['width']*4,min(256,cfg['width']*4+12)]
            jobs.append({'index':i,'config':cfg,'strides':strides,'module_sha256':'renderer-'+str(i)});checkers.append({'module_sha256':'checker-'+str(i)})
            for s,stride in enumerate(strides):
                raw=expected(cfg,stride);canvas=straight(raw,cfg,stride)
                for r in range(2):
                    (source/('frame-%d-%d-%d.raw'%(i,s,r))).write_bytes(raw)
                    if (cfg['width'],cfg['height'],stride)==(17,9,80):(source/('native-%d-%d-%d.raw'%(i,s,r))).write_bytes(raw)
                    rows.append({'job':i,'stride_index':s,'repeat':r,'capacity':16384,'rendered':stride*cfg['height'],'allocation':encode(raw),'straight':encode(canvas),'canvas':encode(canvas),'context':{'alpha':True,'colorSpace':'srgb'},'image_color_space':'srgb'})
            invalid.extend({'job':i,'index':k,'stride':stride,'result':0,'allocation':encode(expected(cfg,strides[0]))} for k,stride in enumerate((0,cfg['width']*4-1,257,0xffffffff)))
            controls.extend({'job':i,'stride_index':s,'mutation':m,'count':1 if m else 0} for s in range(2) for m in range(5));aggregates.append({'job':i,'count':8})
            negative.extend({'job':i,'index':k,'stride_index':s,'mutation':m,'count':0xffffffff} for k,(s,m) in enumerate(((2,0),(0,5),(0xffffffff,0),(0,0xffffffff))))
        return jobs,checkers,{'nonce':'owned','repeat':0,'origin':'http://127.0.0.1:42','user_agent':'unit fixture, not browser evidence','renderer_hashes':[j['module_sha256'] for j in jobs],'checker_hashes':[j['module_sha256'] for j in checkers],'imports':0,'rows':rows,'invalid':invalid,'controls':controls,'aggregates':aggregates,'checker_invalid':negative}
    def check(self,source,jobs,checkers,report):return inspect(report,jobs,checkers,'owned',0,'http://127.0.0.1:42',source)
    def test_counts_and_independent_unpremultiplication(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp);j,c,r=self.fixture(source);v=self.check(source,j,c,r)
            self.assertEqual((v['allocation_bytes'],v['canvas_bytes'],v['native_bytes']),(1048576,99824,20160))
        self.assertEqual(straight(bytes([64,0,32,128]),{'width':1,'height':1},4),bytes([128,0,64,128]))
        self.assertEqual(straight(bytes([0,0,0,0]),{'width':1,'height':1},4),bytes(4))
    def test_allocation_canvas_and_invalid_corruption(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp);j,c,r=self.fixture(source)
            for offset in (0,3,68,79,720,16383):
                bad=copy.deepcopy(r);raw=bytearray(base64.b64decode(bad['rows'][2]['allocation']));raw[offset]^=1;bad['rows'][2]['allocation']=base64.b64encode(raw).decode()
                with self.assertRaises(ValueError):self.check(source,j,c,bad)
            for field in ('straight','canvas'):
                bad=copy.deepcopy(r);bad['rows'][0][field]=base64.b64encode(b'bad').decode()
                with self.assertRaises(ValueError):self.check(source,j,c,bad)
            bad=copy.deepcopy(r);bad['invalid'][0]['allocation']=base64.b64encode(b'bad').decode()
            with self.assertRaises(ValueError):self.check(source,j,c,bad)
    def test_identity_inventory_integer_counts_and_mode(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp);j,c,r=self.fixture(source)
            for k,v in [('repeat',False),('nonce','old'),('imports',False),('renderer_hashes',[]),('checker_hashes',[]),('rows',[])]:
                with self.assertRaises(ValueError):self.check(source,j,c,{**r,k:v})
            for field,key,value in [('controls','count',False),('aggregates','count',7),('checker_invalid','count',0),('rows','repeat',False),('invalid','result',True)]:
                bad=copy.deepcopy(r);bad[field][0][key]=value
                with self.assertRaises(ValueError):self.check(source,j,c,bad)
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='browser-primary-source-subset')
        for params in ({'primary_browser_control':1},{'primary_browser_control':True,'primary_source_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
