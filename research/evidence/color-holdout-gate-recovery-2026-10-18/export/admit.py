"""Unchanged independent predictions for owned exported providers/readback."""
import hashlib,json,math,re,struct
from pathlib import Path
from record_admit import parsed,record,integer,need
SAMPLES=[[.0625,.375,.8125],[.2,.6,.9],[.0625,.375,.8125]]
def expected(mode,rgb):
 if mode==0:
  encoded=[12.92*x if x<=.0031308 else 1.055*math.pow(x,1/2.4)-.055 for x in rgb]
  components=[int(math.floor(x*255+.5)) for x in encoded]+[255]
  return bytes(components)*153,[x/255 for x in components]
 pixel=struct.pack('<4e',*rgb,1);return pixel*153,list(struct.unpack('<4e',pixel))
def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f)
 need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256'])
 rows=[parsed(x) for x in raw.decode().splitlines()];need(len(rows)==6);names=[];buffers={};results=[]
 for index,row in enumerate(rows):
  mode=index//3;phase=index%3;rgb=SAMPLES[phase];provider,channels=expected(mode,rgb);bits=8 if mode==0 else 16
  ints=['pid','mode','phase','width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes','provider_bytes','image_width','image_height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','image_alpha_info']
  need(all(integer(row[k]) for k in ints) and [row[k] for k in ['pid','mode','phase']]==[pid,mode,phase])
  need(type(row['input_linear']) is list and len(row['input_linear'])==3 and all(type(x) in (int,float) and math.isfinite(x) for x in row['input_linear']) and row['input_linear']==rgb)
  need([row[k] for k in ['width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']]==[17,9,288,32,128,8449,1,4096] and row['color_space']=='kCGColorSpaceLinearSRGB')
  need([row[k] for k in ['image_width','image_height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','image_alpha_info','provider_bytes']]==[17,9,17*bits//2,bits,bits*4,1 if mode==0 else 4353,1,len(provider)])
  need(row['image_color_space']==('kCGColorSpaceLinearSRGB' if mode==0 else 'kCGColorSpaceExtendedLinearSRGB'))
  provider_name='mode%d-phase%d-provider.raw'%(mode,phase);name='mode%d-phase%d-readback.raw'%(mode,phase);need(row['provider_file']==provider_name and row['file']==name)
  names.extend([provider_name,name]);p=root/'owned-documents'/provider_name;q=root/'owned-documents'/name;need(not p.is_symlink() and not q.is_symlink());actual=p.read_bytes();data=q.read_bytes()
  need(hashlib.sha256(actual).hexdigest()==row['provider_sha256'] and hashlib.sha256(data).hexdigest()==row['sha256'])
  need(actual==provider)
  readback=bytearray(b'\xa5'*4096);pixel=struct.pack('<4f',*channels)
  for y in range(9):readback[y*288:y*288+272]=pixel*17
  need(data==readback);buffers[(mode,phase)]=(actual,data);results.append({'mode':mode,'phase':phase,'provider_bytes':len(actual),'expected_readback_pixel':list(struct.unpack('<4f',pixel))})
 need({p.name for p in (root/'owned-documents').iterdir()}==set(names))
 for mode in range(2):need(buffers[(mode,0)]==buffers[(mode,2)])
 return {'export_predictions_admitted':True,'provider_bytes_compared':5508,'readback_bytes_compared':24576,'full_bytes_compared':30084,'readback_padding_bytes':864,'readback_tail_bytes':9024,'results':results,'scope':'Declared opaque mixed provider/readback samples only','renderer_internal_cause_proven':False,'display_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
