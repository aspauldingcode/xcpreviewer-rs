"""Full float32 linear-sRGB destination oracle; CGImage storage is measured metadata."""
import json,re,struct
from pathlib import Path
from record_admit import parsed,record,integer,need

def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f);need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256']);rows=[parsed(x) for x in raw.decode().splitlines()];need(len(rows)==12)
 names=[];formats={};classifications=[]
 numeric=['pid','mode','phase','route','callbacks','width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes','image_width','image_height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','image_alpha_info']
 for index,row in enumerate(rows):
  mode=index//6;phase=(index%6)//2;route=index%2;high=phase==1
  need(all(integer(row[k]) for k in numeric));need([row[k] for k in ['pid','mode','phase','route']]==[pid,mode,phase,route] and row['high'] is high and row['callbacks']==route)
  need(row['reported_size']==[17,9] and all(type(x) in (int,float) for x in row['reported_size']))
  need([row[k] for k in ['width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']]==[17,9,288,32,128,8449,1,4096] and row['color_space']=='kCGColorSpaceLinearSRGB')
  need(row['image_width']==17 and row['image_height']==9 and row['image_bits_per_component'] in [8,16,32] and 3*row['image_bits_per_component']<=row['image_bits_per_pixel']<=4*row['image_bits_per_component'] and row['image_stride']>=17*row['image_bits_per_pixel']//8 and row['image_bitmap_info']>=0 and 0<=row['image_alpha_info']<=7 and type(row['image_color_space']) is str and 0<len(row['image_color_space'])<200)
  name='mode%d-phase%d-route%d.raw'%(mode,phase,route);need(row['file']==name);names.append(name);path=root/'owned-documents'/name
  candidates=[('exact',0.5 if high else 0.25)]
  if mode==0:candidates.append(('quantized8',128/255 if high else 64/255))
  matched=[]
  for label,value in candidates:
   expected=bytearray([0xa5]*4096);pixel=struct.pack('<4f',value,value,value,1)
   for y in range(9):expected[y*288:y*288+272]=pixel*17
   if path.is_file() and not path.is_symlink() and path.read_bytes()==expected:matched.append(label)
  need(len(matched)==1)
  classifications.append({'mode':mode,'phase':phase,'route':route,'classification':matched[0]})
  fmt={k:row[k] for k in row if k.startswith('image_')}
  if mode in formats:need(formats[mode]==fmt)
  else:formats[mode]=fmt
 need({p.name for p in (root/'owned-documents').iterdir()}==set(names))
 for mode in range(2):
  for route in range(2):need((root/'owned-documents'/('mode%d-phase0-route%d.raw'%(mode,route))).read_bytes()==(root/'owned-documents'/('mode%d-phase2-route%d.raw'%(mode,route))).read_bytes())
 return {'float32_gray_allocations_admitted':True,'allocations':12,'full_bytes_compared':49152,'padding_bytes':1728,'unused_tail_bytes':18048,'image_storage_by_mode':formats,'classifications':classifications,'within_fixture_quarter_half_quarter_restored':True,'cgimage_provider_bytes_qualified':False,'display_capture_qualified':False,'native_canvas_protocol_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
