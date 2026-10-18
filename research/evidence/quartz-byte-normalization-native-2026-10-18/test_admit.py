import copy,hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from admit import admitted
P=Path(__file__).parent
sha=lambda x:hashlib.sha256(x).hexdigest()
class Controls(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.r=Path(self.temp.name)
  for name in ['probe.swift','source-input.raw','prospective-division.raw','prospective-reciprocal.raw']:shutil.copy2(P/name,self.r/name)
  d=self.r/'owned-documents';d.mkdir();shutil.copy2(P/'source-input.raw',d/'source.raw')
  data=(P/'prospective-reciprocal.raw').read_bytes()
  for phase in range(2):(d/('phase%d.raw'%phase)).write_bytes(data)
  rows=[{'pid':4242,'phase':phase,'file':'phase%d.raw'%phase,'width':256,'height':3,'stride':4112,'allocation_bytes':16384,'sha256':sha(data),'color_space':'kCGColorSpaceLinearSRGB','bitmap_info':8449,'source_sha256':sha((P/'source-input.raw').read_bytes())} for phase in range(2)]
  for phase in ['compile','output-valid','fixture']:
   raw=''.join(json.dumps(v)+'\n' for v in rows) if phase=='fixture' else json.dumps({'pid':4242,'status':'owned_output_control'})+'\n' if phase=='output-valid' else ''
   err='owned_tree_pid:4242\n' if phase!='compile' else ''
   row={'phase':phase,'source_sha256':sha((P/'probe.swift').read_bytes()),'binary_sha256':'1'*64,'error':None,'args':['--fixture',str(d)] if phase=='fixture' else ['--output-control','output-valid'],'record':{'report':{'kind':'complete','target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stdout':raw,'stdoutBytes':len(raw),'stdoutSha256':sha(raw.encode()),'stderr':err,'stderrBytes':len(err),'stderrSha256':sha(err.encode())}}
   (self.r/(phase+'-record.json')).write_text(json.dumps(row));(self.r/(phase+'-outer.json')).write_text(json.dumps({'node_exit':0}))
 def write_fixture(self,v):
  row=json.loads((self.r/'fixture-record.json').read_text());raw=''.join(json.dumps(x)+'\n' for x in v);row['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=sha(raw.encode()));(self.r/'fixture-record.json').write_text(json.dumps(row))
 def test_positive_and_division_countermodel(self):
  result=admitted(self.r);self.assertTrue(result['measurement_receipts_admitted']);self.assertEqual([x['model_mismatch_bytes']['reciprocal'] for x in result['results']],[0,0]);self.assertGreater(result['results'][0]['model_mismatch_bytes']['division'],0)
  data=(self.r/'prospective-division.raw').read_bytes();rows=[]
  for phase in range(2):
   (self.r/'owned-documents'/('phase%d.raw'%phase)).write_bytes(data)
  f=json.loads((self.r/'fixture-record.json').read_text());rows=[json.loads(x) for x in f['record']['stdout'].splitlines()]
  for row in rows:row['sha256']=sha(data)
  self.write_fixture(rows);result=admitted(self.r);self.assertEqual([x['model_mismatch_bytes']['division'] for x in result['results']],[0,0])
 def test_metadata_faults(self):
  f=json.loads((self.r/'fixture-record.json').read_text());rows=[json.loads(x) for x in f['record']['stdout'].splitlines()]
  for key,value in [('pid',True),('phase',True),('width',255),('height',4),('stride',4096),('allocation_bytes',12336),('bitmap_info',1),('color_space','sRGB'),('file','../phase0.raw'),('source_sha256','0'*64),('sha256','0'*64)]:
   bad=copy.deepcopy(rows);bad[0][key]=value;self.write_fixture(bad)
   with self.subTest(key=key),self.assertRaises(Exception):admitted(self.r)
  self.write_fixture(rows)
 def test_bytes_and_repeat_faults(self):
  path=self.r/'owned-documents/phase0.raw';original=path.read_bytes()
  for offset in [0,4096,12336,16383]:
   bad=bytearray(original);bad[offset]^=1;path.write_bytes(bad)
   with self.subTest(offset=offset),self.assertRaises(Exception):admitted(self.r)
  path.write_bytes(original)
  f=json.loads((self.r/'fixture-record.json').read_text());rows=[json.loads(x) for x in f['record']['stdout'].splitlines()]
  bad=bytearray(original);bad[4096]^=1
  for phase in range(2):(self.r/'owned-documents'/('phase%d.raw'%phase)).write_bytes(bad);rows[phase]['sha256']=sha(bad)
  self.write_fixture(rows)
  with self.assertRaises(Exception):admitted(self.r)
 def test_receipt_faults(self):
  p=self.r/'fixture-record.json';base=json.loads(p.read_text())
  for field,value in [('target_code',False),('drained',False),('remaining_observed',1),('kind','timeout')]:
   bad=copy.deepcopy(base);bad['record']['report'][field]=value;p.write_text(json.dumps(bad))
   with self.subTest(field=field),self.assertRaises(Exception):admitted(self.r)
  p.write_text(json.dumps(base));(self.r/'output-valid-record.json').unlink()
  with self.assertRaises(Exception):admitted(self.r)
if __name__=='__main__':unittest.main()
