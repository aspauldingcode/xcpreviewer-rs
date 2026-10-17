"""Direct Quartz exactness and independent historical comparisons; bridge values stay observations."""
import hashlib,json,math,re,struct
from pathlib import Path
from record_admit import parsed,record,integer,need
PARENT_SEAL='39a4e3b488eca1bd1c4302daaff480f25b8f37050b1a87c72aa36132cbe0ee6e'

def admitted(root):
 root=Path(root);reference=parsed((root/'references.json').read_text());sealfile=root/'references/parent-seal.json';need(hashlib.sha256(sealfile.read_bytes()).hexdigest()==PARENT_SEAL);parent=parsed(sealfile.read_text())
 expected_refs={('%s-phase%d.raw'%(kind,phase)):{'parent_path':'gray/owned-documents/mode0-phase%d-route%d.raw'%(phase,route)} for phase in range(3) for kind,route in [('callback',1),('cgdraw',0)]}
 need(reference['files']==expected_refs)
 refs={}
 for name,entry in reference['files'].items():
  data=(root/'references'/name).read_bytes();need(hashlib.sha256(data).hexdigest()==parent['files'][entry['parent_path']] and len(data)==4096);refs[name]=data
 f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());record(c,False);raw,pid=record(f);need(type(f['binary_sha256']) is str and re.fullmatch('[0-9a-f]{64}',f['binary_sha256']) and f['binary_sha256']==c['binary_sha256']);rows=[parsed(s) for s in raw.decode().splitlines()];need(len(rows)==12);names=[];comparisons=[];values={}
 for index,row in enumerate(rows):
  phase=index//4;route=index%4;high=phase==1
  need(all(integer(row[k]) for k in ['pid','phase','route','width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']))
  need([row[k] for k in ['pid','phase','route']]==[pid,phase,route] and row['high'] is high and [row[k] for k in ['width','height','stride','bits_per_component','bits_per_pixel','bitmap_info','alpha_info','allocation_bytes']]==[17,9,288,32,128,8449,1,4096] and row['color_space']=='kCGColorSpaceLinearSRGB')
  need(type(row['source_color_space']) is str and 0<len(row['source_color_space'])<200 and type(row['source_components']) is list and len(row['source_components']) in [2,4] and all(type(x) in (int,float) and math.isfinite(x) for x in row['source_components']))
  name='phase%d-route%d.raw'%(phase,route);need(row['file']==name);names.append(name);path=root/'owned-documents'/name;need(path.is_file() and not path.is_symlink());data=path.read_bytes();need(len(data)==4096 and hashlib.sha256(data).hexdigest()==row['sha256'])
  expected=bytearray([0xa5]*4096);value=0.5 if high else 0.25;pixel=struct.pack('<4f',value,value,value,1)
  for y in range(9):expected[y*288:y*288+272]=pixel*17
  if route==0:need(data==expected)
  first=data[:16];v=struct.unpack('<4f',first);need(all(math.isfinite(x) and 0<=x<=1 for x in v) and v[0]==v[1]==v[2] and v[3]==1)
  for y in range(9):need(data[y*288:y*288+272]==first*17 and data[y*288+272:y*288+288]==b'\xa5'*16)
  need(data[2592:]==b'\xa5'*1504);values[(phase,route)]=v[0]
  targets={'analytic_direct':bytes(expected),'previous_callback':refs['callback-phase%d.raw'%phase],'previous_linear_cg_draw':refs['cgdraw-phase%d.raw'%phase]}
  metrics={k:sum(a!=b for a,b in zip(data,target)) for k,target in targets.items()}
  comparisons.append({'phase':phase,'route':route,'observed_first_rgba':list(v),'mismatch_bytes':metrics,'matches':{k:count==0 for k,count in metrics.items()}})
 need({p.name for p in (root/'owned-documents').iterdir()}==set(names))
 for route in range(4):
  need(values[(1,route)]>values[(0,route)] and (root/'owned-documents'/('phase0-route%d.raw'%route)).read_bytes()==(root/'owned-documents'/('phase2-route%d.raw'%route)).read_bytes())
 return {'measurement_receipts_admitted':True,'direct_quartz_exact_qualified':True,'direct_full_bytes':12288,'all_full_bytes_compared':49152,'padding_bytes':1728,'unused_tail_bytes':18048,'comparisons':comparisons,'routes_matching_previous_callback':[route for route in range(4) if all(x['matches']['previous_callback'] for x in comparisons if x['route']==route)],'bridge_numeric_correctness_qualified':False,'renderer_internal_cause_qualified':False,'display_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
