"""Analytical direct baseline and independent public half-source holdout comparison."""
import hashlib,json,math,re,struct
from pathlib import Path
from record_admit import parsed,record,integer,need
SAMPLES=[[.0625,.375,.8125],[.2,.6,.9],[.0625,.375,.8125]]

def predicted(rgb):
 encoded=[12.92*x if x<=.0031308 else 1.055*math.pow(x,1/2.4)-.055 for x in rgb]
 bits=[struct.unpack('<H',struct.pack('<e',x))[0] for x in encoded]
 values=[struct.unpack('<e',struct.pack('<H',x))[0] for x in bits]
 return bits,values

def admitted(root):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f)
 need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256'])
 rows=[parsed(s) for s in raw.decode().splitlines()];need(len(rows)==18);names=[];buffers={}
 for index,row in enumerate(rows):
  mode=index//9;phase=index%9//3;route=index%3;rgb=SAMPLES[phase];bits,values=predicted(rgb)
  need(all(integer(row[k]) for k in ['pid','mode','phase','route','callbacks','width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']))
  need([row[k] for k in ['pid','mode','phase','route']]==[pid,mode,phase,route])
  need([row[k] for k in ['width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']]==[17,9,288,32,128,8449,1,4096])
  for key,expected in [('input_linear',rgb),('encoded_half_components',values),('reported_size',[17,9])]:
   need(type(row[key]) is list and len(row[key])==len(expected) and all(type(x) in (int,float) and math.isfinite(x) for x in row[key]) and row[key]==expected)
  need(type(row['encoded_half_bits']) is list and len(row['encoded_half_bits'])==3 and all(integer(x,b) for x,b in zip(row['encoded_half_bits'],bits)))
  need(row['callbacks']==(1 if route==2 else 0) and row['color_space']=='kCGColorSpaceLinearSRGB')
  name='mode%d-phase%d-route%d.raw'%(mode,phase,route);names.append(name);need(row['file']==name);p=root/'owned-documents'/name
  data=p.read_bytes();need(not p.is_symlink() and len(data)==4096 and hashlib.sha256(data).hexdigest()==row['sha256'])
  first=data[:16];pixel=struct.unpack('<4f',first);need(all(math.isfinite(x) and 0<=x<=1 for x in pixel) and pixel[3]==1)
  for y in range(9):need(data[y*288:y*288+272]==first*17 and data[y*288+272:y*288+288]==b'\xa5'*16)
  need(data[2592:]==b'\xa5'*1504)
  if route==0:
   expected=bytearray(b'\xa5'*4096);analytic=struct.pack('<4f',*rgb,1)
   for y in range(9):expected[y*288:y*288+272]=analytic*17
   need(data==expected)
  buffers[(mode,phase,route)]=data
 need({p.name for p in (root/'owned-documents').iterdir()}==set(names))
 for mode in range(2):
  for route in range(3):need(buffers[(mode,0,route)]==buffers[(mode,2,route)])
 comparisons=[]
 for mode in range(2):
  for phase in range(3):
   half=buffers[(mode,phase,1)];callback=buffers[(mode,phase,2)]
   comparisons.append({'mode':mode,'phase':phase,'matches':half==callback,'mismatch_bytes':sum(a!=b for a,b in zip(half,callback)),'half_pixel':list(struct.unpack('<4f',half[:16])),'callback_pixel':list(struct.unpack('<4f',callback[:16]))})
 return {'measurement_receipts_admitted':True,'full_bytes_compared':73728,'analytic_direct_bytes':24576,'padding_bytes':2592,'tail_bytes':27072,'comparisons':comparisons,'half_source_sufficient_for_holdouts':all(x['matches'] for x in comparisons),'image_renderer_internal_half_precision_proven':False,'display_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
