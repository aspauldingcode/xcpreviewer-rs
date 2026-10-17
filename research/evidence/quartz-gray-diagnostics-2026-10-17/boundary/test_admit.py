import hashlib,json,shutil,struct,tempfile,unittest
from pathlib import Path
from admit import admitted
HERE=Path(__file__).parent

def encode(r,rows):
 raw=''.join(json.dumps(x)+'\n' for x in rows);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
def build(p):
 shutil.copytree(HERE/'references',p/'references');shutil.copyfile(HERE/'references.json',p/'references.json');(p/'owned-documents').mkdir()
 r={'error':None,'binary_sha256':'a'*64,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stderr':'owned_tree_pid:123\n'}};rows=[]
 for phase in range(3):
  high=phase==1;value=0.5 if high else 0.25
  for route in range(4):
   name='phase%d-route%d.raw'%(phase,route);data=bytearray([0xa5]*4096);pixel=struct.pack('<4f',value,value,value,1)
   for y in range(9):data[y*288:y*288+272]=pixel*17
   if route:data=bytearray((p/'references'/('callback-phase%d.raw'%phase)).read_bytes())
   (p/'owned-documents'/name).write_bytes(data)
   rows.append(dict(pid=123,phase=phase,route=route,high=high,file=name,sha256=hashlib.sha256(data).hexdigest(),width=17,height=9,stride=288,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,alpha_info=1,allocation_bytes=4096,color_space='kCGColorSpaceLinearSRGB',source_color_space='kCGColorSpaceLinearSRGB',source_components=[value,value,value,1]))
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class AdmissionTests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);build(p);v=admitted(p);self.assertEqual(v['direct_full_bytes'],12288);self.assertEqual(v['routes_matching_previous_callback'],[1,2,3]);self.assertFalse(v['bridge_numeric_correctness_qualified'])
 def test_unknown_uniform_is_not_numeric_qualification(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);r,rows=build(p)
   for phase in range(3):
    value=0.7 if phase==1 else 0.3;data=bytearray([0xa5]*4096);pixel=struct.pack('<4f',value,value,value,1)
    for y in range(9):data[y*288:y*288+272]=pixel*17
    name='phase%d-route3.raw'%phase;(p/'owned-documents'/name).write_bytes(data);rows[phase*4+3]['sha256']=hashlib.sha256(data).hexdigest()
   encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));v=admitted(p);self.assertNotIn(3,v['routes_matching_previous_callback']);self.assertFalse(v['bridge_numeric_correctness_qualified']);self.assertTrue(all(not any(x['matches'].values()) for x in v['comparisons'] if x['route']==3))
 def test_prior_label_rebinding_counterexample(self):
  import importlib.util
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);build(p);f=p/'references.json';v=json.loads(f.read_text());v['files']['callback-phase0.raw']['parent_path']='gray/owned-documents/mode0-phase0-route0.raw';f.write_text(json.dumps(v));shutil.copyfile(p/'references/cgdraw-phase0.raw',p/'references/callback-phase0.raw')
   spec=importlib.util.spec_from_file_location('prior_checker',HERE/'pre-fix-admit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   self.assertTrue(m.admitted(p)['measurement_receipts_admitted'])
   with self.assertRaises(ValueError):admitted(p)
 def test_faults(self):
  faults=['wait','drain','remaining','abort','binary','hash','bytes','pid','phase','route','high','stride','bpc','bitmap','space','allocation','source_space','source_components','source_bool','file_hash','pixel','direct_pixel','padding','tail','alpha','nonfinite','nonuniform','nonmonotone','restoration','extra_file','missing_file','reference','duplicate','typed','rows','reference_relabel']
  for fault in faults:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    p=Path(t);r,rows=build(p);row=rows[-1]
    if fault=='wait':r['record']['report']['target_code']=7
    elif fault=='drain':r['record']['report']['drained']=False
    elif fault=='remaining':r['record']['report']['remaining_observed']=1
    elif fault=='abort':r['record']['privateAbortRequested']=True
    elif fault=='binary':r['binary_sha256']='b'*64
    elif fault=='hash':r['record']['stdoutSha256']='0'*64
    elif fault=='bytes':r['record']['stdoutBytes']+=1
    elif fault=='pid':row['pid']=999
    elif fault=='phase':row['phase']=1
    elif fault=='route':row['route']=0
    elif fault=='high':row['high']=True
    elif fault=='stride':row['stride']=272
    elif fault=='bpc':row['bits_per_component']=16
    elif fault=='bitmap':row['bitmap_info']=1
    elif fault=='space':row['color_space']='kCGColorSpaceSRGB'
    elif fault=='allocation':row['allocation_bytes']=2592
    elif fault=='source_space':row['source_color_space']=''
    elif fault=='source_components':row['source_components']=[]
    elif fault=='source_bool':row['source_components'][0]=True
    elif fault=='file_hash':row['sha256']='0'*64
    elif fault in ['pixel','direct_pixel','padding','tail','alpha','nonfinite','nonuniform']:
     target=rows[0] if fault=='direct_pixel' else row;f=p/'owned-documents'/target['file'];v=bytearray(f.read_bytes())
     if fault=='nonfinite':v[:4]=struct.pack('<f',float('nan'))
     else:v[{'pixel':0,'direct_pixel':0,'padding':272,'tail':4095,'alpha':12,'nonuniform':16}[fault]]^=1
     f.write_bytes(v);target['sha256']=hashlib.sha256(v).hexdigest()
    elif fault in ['nonmonotone','restoration']:
     target=rows[7] if fault=='nonmonotone' else row;phase=1 if fault=='nonmonotone' else 2;data=(p/'owned-documents/phase0-route3.raw').read_bytes() if fault=='nonmonotone' else (p/'owned-documents/phase1-route3.raw').read_bytes();(p/'owned-documents'/target['file']).write_bytes(data);target['sha256']=hashlib.sha256(data).hexdigest()
    elif fault=='extra_file':(p/'owned-documents/extra.raw').write_bytes(b'extra')
    elif fault=='missing_file':(p/'owned-documents'/row['file']).unlink()
    elif fault=='reference':f=p/'references/callback-phase0.raw';v=bytearray(f.read_bytes());v[0]^=1;f.write_bytes(v)
    elif fault=='reference_relabel':
     f=p/'references.json';v=json.loads(f.read_text());v['files']['callback-phase0.raw']['parent_path']='gray/owned-documents/mode0-phase0-route0.raw';f.write_text(json.dumps(v));shutil.copyfile(p/'references/cgdraw-phase0.raw',p/'references/callback-phase0.raw')
    elif fault=='typed':row['width']=17.0
    elif fault=='rows':rows.pop()
    if fault not in ['hash','bytes']:encode(r,rows)
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"pid": 123','"pid": 123, "pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError,FileNotFoundError)):admitted(p)
if __name__=='__main__':unittest.main()
