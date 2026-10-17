import hashlib,json,shutil,struct,tempfile,unittest
from pathlib import Path
from admit import admitted
P=Path(__file__).parent

def encode(r,rows):
 raw=''.join(json.dumps(x)+'\n' for x in rows);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
def build(p):
 shutil.copytree(P/'references',p/'references');shutil.copyfile(P/'references.json',p/'references.json');(p/'owned-documents').mkdir();rows=[]
 r={'error':None,'binary_sha256':'a'*64,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stderr':'owned_tree_pid:123\n'}}
 for phase in range(3):
  high=phase==1;bits=14818 if high else 14412;v=struct.unpack('<e',struct.pack('<H',bits))[0]
  for route in range(2):
   data=(p/'references'/('%s-phase%d.raw'%('quartz' if route==0 else 'callback',phase))).read_bytes();name='phase%d-route%d.raw'%(phase,route);(p/'owned-documents'/name).write_bytes(data)
   rows.append(dict(pid=123,phase=phase,route=route,high=high,file=name,sha256=hashlib.sha256(data).hexdigest(),width=17,height=9,stride=288,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,alpha_info=1,allocation_bytes=4096,color_space='kCGColorSpaceLinearSRGB',source_color_space='kCGColorSpaceSRGB',source_components=[v,v,v,1],half_bits=[bits]*3))
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class Tests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);build(p);self.assertTrue(admitted(p)['half_source_matches_all_previous_callbacks'])
 def test_nonmatching_countermodel(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);r,rows=build(p)
   for phase in range(3):
    data=(p/'references'/('quartz-phase%d.raw'%phase)).read_bytes();(p/'owned-documents'/rows[phase*2+1]['file']).write_bytes(data);rows[phase*2+1]['sha256']=hashlib.sha256(data).hexdigest()
   encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));self.assertFalse(admitted(p)['half_source_matches_all_previous_callbacks'])
 def test_faults(self):
  for fault in ['wait','hash','pid','half_bits','components','source_space','layout','padding','tail','alpha','uniformity','baseline','reference','manifest','restore','duplicate','component_bool','component_overflow']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    p=Path(t);r,rows=build(p);row=rows[-1]
    if fault=='wait':r['record']['report']['target_code']=7
    elif fault=='hash':r['record']['stdoutSha256']='0'*64
    elif fault=='pid':row['pid']=999
    elif fault=='half_bits':row['half_bits'][0]+=1
    elif fault=='component_bool':row['source_components'][3]=True
    elif fault=='component_overflow':rows[0]['source_components'][0]=1e308
    elif fault=='components':row['source_components'][0]+=0.1
    elif fault=='source_space':row['source_color_space']='wrong'
    elif fault=='layout':row['stride']=272
    elif fault=='manifest':f=p/'references.json';f.write_bytes(f.read_bytes()+b' ')
    elif fault=='reference':f=p/'references/quartz-phase0.raw';v=bytearray(f.read_bytes());v[0]^=1;f.write_bytes(v)
    elif fault in ['padding','tail','alpha','uniformity','baseline']:
     target=rows[0] if fault=='baseline' else row;f=p/'owned-documents'/target['file'];v=bytearray(f.read_bytes());v[{'padding':272,'tail':4095,'alpha':12,'uniformity':16,'baseline':0}[fault]]^=1;f.write_bytes(v);target['sha256']=hashlib.sha256(v).hexdigest()
    elif fault=='restore':data=(p/'owned-documents/phase1-route1.raw').read_bytes();(p/'owned-documents'/row['file']).write_bytes(data);row['sha256']=hashlib.sha256(data).hexdigest()
    if fault!='hash':encode(r,rows)
    if fault=='component_overflow':
     raw=r['record']['stdout'].replace('1e+308','1e999',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"pid": 123','"pid": 123, "pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError)):admitted(p)
if __name__=='__main__':unittest.main()
