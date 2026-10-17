"""Paired unquantized/IEEE-half sRGB source; compare full outputs to independent earlier captures."""
import hashlib,json,re,struct
from pathlib import Path
from record_admit import parsed,record,integer,need

def admitted(root):
 root=Path(root);need(hashlib.sha256((root/'references.json').read_bytes()).hexdigest()=='581c2694e288b970ed075e6ffe971c05db8c3a469ce23d3a63dbfb7b3507f139');refs=parsed((root/'references.json').read_text());f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f);need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256']);rows=[parsed(s) for s in raw.decode().splitlines()];need(len(rows)==6);names=[];comparisons=[]
 for index,row in enumerate(rows):
  phase=index//2;route=index%2;high=phase==1;bits=14818 if high else 14412;value=struct.unpack('<e',struct.pack('<H',bits))[0]
  need(all(integer(row[k]) for k in ['pid','phase','route','width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']))
  need([row[k] for k in ['pid','phase','route']]==[pid,phase,route] and row['high'] is high and [row[k] for k in ['width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']]==[17,9,288,32,128,8449,1,4096] and row['color_space']=='kCGColorSpaceLinearSRGB')
  need(row['source_color_space']=='kCGColorSpaceSRGB' and row['half_bits']==[bits]*3 and all(integer(x,bits) for x in row['half_bits']))
  if route==1:need(row['source_components']==[value,value,value,1])
  else:need(len(row['source_components'])==4 and all(type(x) in (int,float) for x in row['source_components']))
  name='phase%d-route%d.raw'%(phase,route);names.append(name);need(row['file']==name);p=root/'owned-documents'/name;data=p.read_bytes();need(not p.is_symlink() and len(data)==4096 and hashlib.sha256(data).hexdigest()==row['sha256'])
  previous=root/'references'/('quartz-phase%d.raw'%phase);callback=root/'references'/('callback-phase%d.raw'%phase)
  for source in [previous,callback]:need(hashlib.sha256(source.read_bytes()).hexdigest()==refs['files'][source.name]['sha256'])
  direct=previous.read_bytes();target=callback.read_bytes();need(len(direct)==len(target)==4096)
  if route==0:need(data==direct)
  first=data[:16];pixel=struct.unpack('<4f',first);need(pixel[0]==pixel[1]==pixel[2] and 0<pixel[0]<1 and pixel[3]==1)
  for y in range(9):need(data[y*288:y*288+272]==first*17 and data[y*288+272:y*288+288]==b'\xa5'*16)
  need(data[2592:]==b'\xa5'*1504)
  comparisons.append({'phase':phase,'route':route,'observed_first_rgba':list(pixel),'matches_previous_callback':data==target,'callback_mismatch_bytes':sum(a!=b for a,b in zip(data,target)),'matches_unquantized_quartz':data==direct})
 need({p.name for p in (root/'owned-documents').iterdir()}==set(names))
 for route in range(2):need((root/'owned-documents'/('phase0-route%d.raw'%route)).read_bytes()==(root/'owned-documents'/('phase2-route%d.raw'%route)).read_bytes())
 return {'measurement_admitted':True,'full_bytes_compared':24576,'padding_bytes':864,'tail_bytes':9024,'comparisons':comparisons,'half_source_matches_all_previous_callbacks':all(x['matches_previous_callback'] for x in comparisons if x['route']==1),'image_renderer_internal_half_precision_proven':False,'arbitrary_color_correctness_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
