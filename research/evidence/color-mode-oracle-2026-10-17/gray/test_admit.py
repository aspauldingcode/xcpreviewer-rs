import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from admit import admitted

def encode(r,rows):
 raw=''.join(json.dumps(x)+'\n' for x in rows);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
def build(p):
 r={'error':None,'binary_sha256':'a'*64,'record':{'report':{'target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stderr':'owned_tree_pid:123\n'}};rows=[];(p/'owned-documents').mkdir()
 for index in range(12):
  mode=index//6;phase=(index%6)//2;route=index%2;high=phase==1;name='mode%d-phase%d-route%d.raw'%(mode,phase,route)
  row=dict(pid=123,mode=mode,phase=phase,route=route,high=high,file=name,callbacks=route,reported_size=[17,9],width=17,height=9,stride=288,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,alpha_info=1,allocation_bytes=4096,color_space='kCGColorSpaceLinearSRGB',image_width=17,image_height=9,image_stride=80 if mode==0 else 144,image_bits_per_component=8 if mode==0 else 16,image_bits_per_pixel=32 if mode==0 else 64,image_bitmap_info=8194 if mode==0 else 4353,image_alpha_info=2 if mode==0 else 1,image_color_space='kCGColorSpaceSRGB' if mode==0 else 'kCGColorSpaceExtendedLinearSRGB');rows.append(row)
  data=bytearray([0xa5]*4096);value=(128/255 if high else 64/255) if mode==0 and route==0 else (0.5 if high else 0.25);pixel=struct.pack('<4f',value,value,value,1)
  for y in range(9):data[y*288:y*288+272]=pixel*17
  (p/'owned-documents'/name).write_bytes(data)
 encode(r,rows);(p/'fixture-record.json').write_text(json.dumps(r));(p/'compile-record.json').write_text(json.dumps(r));return r,rows
class AdmissionTests(unittest.TestCase):
 def test_positive(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);build(p);self.assertEqual(admitted(p)['full_bytes_compared'],49152)
 def test_quantized_callback_countermodel(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);build(p)
   for phase in range(3):
    value=128/255 if phase==1 else 64/255;data=bytearray([0xa5]*4096);pixel=struct.pack('<4f',value,value,value,1)
    for y in range(9):data[y*288:y*288+272]=pixel*17
    (p/'owned-documents'/('mode0-phase%d-route1.raw'%phase)).write_bytes(data)
   result=admitted(p);self.assertEqual([x['classification'] for x in result['classifications'] if x['mode']==0 and x['route']==1],['quantized8']*3)
 def test_faults(self):
  faults=['wait','drain','remaining','abort','binary','hash','bytes','pid','mode','phase','route','high','callbacks','geometry','stride','bpc','bpp','bitmap','alpha','space','allocation','image_geometry','image_stride','image_bpc','image_bpp','image_space','image_drift','pixel','padding','tail','stale_high','extra_file','missing_file','duplicate','typed','rows','restoration']
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
    elif fault=='mode':row['mode']=0
    elif fault=='phase':row['phase']=1
    elif fault=='route':row['route']=0
    elif fault=='high':row['high']=True
    elif fault=='callbacks':row['callbacks']=2
    elif fault=='geometry':row['reported_size']=[9,17]
    elif fault=='stride':row['stride']=272
    elif fault=='bpc':row['bits_per_component']=16
    elif fault=='bpp':row['bits_per_pixel']=64
    elif fault=='bitmap':row['bitmap_info']=1
    elif fault=='alpha':row['alpha_info']=0
    elif fault=='space':row['color_space']='kCGColorSpaceSRGB'
    elif fault=='allocation':row['allocation_bytes']=2592
    elif fault=='image_geometry':row['image_width']=9
    elif fault=='image_stride':row['image_stride']=1
    elif fault=='image_bpc':row['image_bits_per_component']=7
    elif fault=='image_bpp':row['image_bits_per_pixel']=16
    elif fault=='image_space':row['image_color_space']=''
    elif fault=='image_drift':row['image_stride']+=16
    elif fault in ['pixel','padding','tail']:
     f=p/'owned-documents'/row['file'];v=bytearray(f.read_bytes());v[{'pixel':0,'padding':272,'tail':4095}[fault]]^=1;f.write_bytes(v)
    elif fault=='stale_high':(p/'owned-documents/mode1-phase1-route0.raw').write_bytes((p/'owned-documents/mode1-phase0-route0.raw').read_bytes())
    elif fault=='extra_file':(p/'owned-documents/extra.raw').write_bytes(b'extra')
    elif fault=='missing_file':(p/'owned-documents'/row['file']).unlink()
    elif fault=='restoration':
     f=p/'owned-documents/mode0-phase2-route1.raw';data=bytearray([0xa5]*4096);pixel=struct.pack('<4f',64/255,64/255,64/255,1)
     for y in range(9):data[y*288:y*288+272]=pixel*17
     f.write_bytes(data)
    elif fault=='typed':row['width']=17.0
    elif fault=='rows':rows.pop()
    if fault not in ['hash','bytes']:encode(r,rows)
    if fault=='duplicate':
     raw=r['record']['stdout'].replace('"pid": 123','"pid": 123, "pid": 123',1);r['record'].update(stdout=raw,stdoutBytes=len(raw),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest())
    (p/'fixture-record.json').write_text(json.dumps(r))
    with self.assertRaises((ValueError,KeyError)):admitted(p)
if __name__=='__main__':unittest.main()
