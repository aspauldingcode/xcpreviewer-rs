"""Public producer contrast; diagnostic comparisons never replace exact expectations."""
from pathlib import Path
import json,hashlib,struct,datetime
from predictions import provider,readback
from phase_prerequisites import parsed,receipt,integer,require as need
H=lambda b:hashlib.sha256(b).hexdigest()
def rows_observed(root,rows):
 p=Path(root);need(type(rows) is list and len(rows)==3,'rows');names=set();results=[];buffers=[]
 for route,row in enumerate(rows):
  keys=['pid','route','provider_bytes','width','height','image_stride','image_bits_per_component','image_bits_per_pixel','image_bitmap_info','stride','allocation_bytes','bits_per_component','bits_per_pixel','bitmap_info']
  need(all(integer(row[k]) for k in keys),'integer metadata')
  need([row[k] for k in keys[1:]]==[route,9408,768,3,3136,8,32,1,12352,49152,32,128,8449],'layout')
  need(row['color_space']=='kCGColorSpaceLinearSRGB' and row['source_color_space']==('kCGColorSpaceLinearSRGB' if route==1 else 'kCGColorSpaceSRGB'),'profile')
  a='route%d-provider.raw'%route;b='route%d-readback.raw'%route;need(row['provider_file']==a and row['file']==b,'file names');names.update([a,b]);ap=p/'owned-documents'/a;bp=p/'owned-documents'/b
  need(not ap.is_symlink() and not bp.is_symlink(),'linked output');src=ap.read_bytes();dst=bp.read_bytes();need(src==provider(route) and H(src)==row['provider_sha256'] and len(dst)==49152 and H(dst)==row['sha256'],'provider/hash')
  for y in range(3):need(dst[y*12352+12288:(y+1)*12352]==b'\xa5'*64,'padding')
  need(dst[37056:]==b'\xa5'*12096,'tail')
  candidates=['identity','iec_srgb'] if route==2 else ['alpha_invariant','transfer_premultiplied'];comparisons=[]
  for c in candidates:
   expected=readback(route,c);diff=[i for i,(x,y) in enumerate(zip(dst,expected)) if x!=y];comparisons.append({'candidate':c,'mismatch_bytes':len(diff),'first_mismatch':diff[0] if diff else None})
  results.append({'route':route,'comparisons':comparisons});buffers.append(dst)
 need({x.name for x in (p/'owned-documents').iterdir()}==names,'inventory')
 primary=all(buffers[i]==readback(i,'alpha_invariant') for i in [0,1]);wrong_discriminated=all(buffers[i]!=readback(i,'transfer_premultiplied') for i in [0,1]);gray=True
 for y in range(3):
  for x in range(768):
   pixel=struct.unpack_from('<4f',buffers[2],y*12352+x*16);gray=gray and all(0.20<v<0.23 for v in pixel[:3]) and pixel[3]==1.0
 return {'primary_alpha_invariant_exact':primary,'transfer_on_premultiplied_candidate_rejected':wrong_discriminated,'opaque_gray_conversion_operational_range':gray,'opaque_gray_bit_exact_model_qualified':any(x['candidate']=='iec_srgb' and x['mismatch_bytes']==0 for x in results[2]['comparisons']),'all_bytes_compared':175680,'provider_bytes':28224,'readback_bytes':147456,'readback_padding':576,'readback_tail':36288,'comparisons':results,'renderer_internal_order_proven':False,'display_qualified':False,'canvas_qualified':False}
def observed(root):
 p=Path(root)
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H((p/n).read_bytes())==h,'source pin')
 c=parsed((p/'compile-record.json').read_text());source=H((p/'probe.c').read_bytes());binary=c['binary_sha256']
 for phase in ['compile','output-valid','fixture']:receipt(p,phase,source,binary)
 rea=parsed((p/'rea-identity.json').read_text());need(rea['owned_binary_sha256']==binary and rea['closed'] is True and rea['architecture']=='arm64','REA identity')
 times=[];deadline=datetime.datetime(2026,10,19,14,10,tzinfo=datetime.timezone.utc)
 for phase in ['compile','output-valid','fixture']:
  v=parsed((p/(phase+'-started.json')).read_text());t=datetime.datetime.fromisoformat(v['started_at']);need(v['phase']==phase and v['deadline_utc']=='2026-10-19T14:10:00Z' and t<deadline,'phase start');times.append(t)
 completed=parsed((p/'completed.json').read_text());t=datetime.datetime.fromisoformat(completed['completed_at']);need(completed['deadline_utc']=='2026-10-19T14:10:00Z' and times==sorted(times) and times[-1]<t<deadline,'completion')
 r=parsed((p/'fixture-record.json').read_text())['record'];rows=[parsed(s) for s in r['stdout'].splitlines()];need(len(rows)==3 and integer(rows[0]['pid']) and rows[0]['pid']>1 and all(x['pid']==rows[0]['pid'] for x in rows) and r['stderr']=='owned_tree_pid:'+str(rows[0]['pid'])+'\n','owned PID/streams')
 return rows_observed(p,rows)
def admit(root):
 result=observed(root);need(result['primary_alpha_invariant_exact'] and result['transfer_on_premultiplied_candidate_rejected'] and result['opaque_gray_conversion_operational_range'],'primary/range contract');return result
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent)))
