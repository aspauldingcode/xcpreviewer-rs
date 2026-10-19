"""Independent frozen arithmetic admission, not renderer internal causation."""
import hashlib,json,re
from pathlib import Path
from phase_prerequisites import receipt
from record_admit import parsed,record,integer,need
from predictions import provider,readback

def admitted(root,diagnostic=False):
 root=Path(root);f=parsed((root/'fixture-record.json').read_text());c=parsed((root/'compile-record.json').read_text());source=hashlib.sha256((root/'probe.c').read_bytes()).hexdigest()
 for phase in ['compile','output-valid','fixture']:receipt(root,phase,source,c['binary_sha256'])
 raw,pid=record(f);need(f['binary_sha256']==c['binary_sha256']);rows=[parsed(x) for x in raw.decode().splitlines()];need(len(rows)==2)
 expected_names=set();buffers={};results=[]
 for route,row in enumerate(rows):
  need(all(integer(row[k]) for k in ['pid','route','provider_bytes','width','height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','stride','allocation_bytes','bits_per_component','bits_per_pixel','bitmap_info']))
  need(row['pid']==pid and row['route']==route and [row[k] for k in ['provider_bytes','width','height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','stride','allocation_bytes','bits_per_component','bits_per_pixel','bitmap_info']]==[12480 if route else 3264,256,3,4160 if route else 1088,32 if route else 8,128 if route else 32,8449 if route else 1,4160,16384,32,128,8449] and row['color_space']=='kCGColorSpaceLinearSRGB')
  a='route%d-provider.raw'%route;b='route%d-readback.raw'%route;need(row['provider_file']==a and row['file']==b);expected_names.update([a,b]);ap=root/'owned-documents'/a;bp=root/'owned-documents'/b;need(not ap.is_symlink() and not bp.is_symlink());actual=ap.read_bytes();data=bp.read_bytes();need(actual==provider(route) and hashlib.sha256(actual).hexdigest()==row['provider_sha256'] and hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==16384)
  comparisons=[]
  for candidate in ['divide','multiply']:
   predicted=readback(candidate);diff=[i for i,(x,y) in enumerate(zip(data,predicted)) if x!=y];comparisons.append({'candidate':candidate,'mismatch_bytes':len(diff),'first_mismatch':diff[0] if diff else None})
  buffers[route]=data;results.append({'route':route,'comparisons':comparisons})
 need({p.name for p in (root/'owned-documents').iterdir()}==expected_names)
 baseline=buffers[1]==readback('divide');matches=[x['candidate'] for x in results[0]['comparisons'] if x['mismatch_bytes']==0]
 if not diagnostic:need(baseline and len(matches)>0)
 return {'normalization_candidates_supported':matches,'float32_baseline_exact':baseline,'full_bytes_compared':48512,'provider_bytes_compared':15744,'readback_bytes_compared':32768,'readback_padding_bytes':384,'readback_tail_bytes':7808,'comparisons':results,'renderer_internal_cause_proven':False,'display_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
