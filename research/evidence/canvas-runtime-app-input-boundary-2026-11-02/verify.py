"""Check retained native UI artifacts; does not perform UI input or run Xcode."""
from pathlib import Path
import json
from PIL import Image

def glyph(r,name,roi):
 im=Image.open(r/name).convert('RGB').crop(roi);mask=Image.new('1',im.size);mask.putdata([max(rgb)<60 for rgb in im.getdata()]);bbox=mask.getbbox();assert bbox;return mask.crop(bbox)
def verify(root):
 r=Path(root);o=json.loads((r/'observations.json').read_text());assert o['owned_app_pid_before']==o['owned_app_pid_after']==46767
 assert o['source_sha256_unchanged']=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef' and not o['source_edited'] and o['controller_available_after']
 assert not o['canvas_input_delivery_qualified'] and not o['canvas_state_preservation_verified']
 assert [o[k] for k in ['native_app_count_before','native_app_count_after','canvas_count_after']]==[0,1,0]
 ax=(r/'host-full-after-ax.txt').read_text();assert 'Canvas baseline Count: 1' in ax and 'PreviewLab.CanvasExamples-1-AppWindow-1' in ax and 'button Increment' in ax
 assert Image.open(r/'host-before.png').size==Image.open(r/'host-after.png').size==(1800,900)
 assert Image.open(r/'canvas-after-host-input.png').size==(2802,1804)
 before=glyph(r,'host-before.png',(800,455,1000,515));after=glyph(r,'host-after.png',(800,455,1000,515));canvas=glyph(r,'canvas-after-host-input.png',(2180,965,2320,1005))
 assert before.size!=after.size and before.size==canvas.size
 a={i for i,p in enumerate(before.getdata()) if p};b={i for i,p in enumerate(canvas.getdata()) if p};iou=len(a&b)/len(a|b)
 return {'artifact_checks':'passed','app_input_positive_control':True,'native_ui_rerun':False,'zero_glyph_mask_iou':iou,'canvas_input_qualified':False,'state_continuity_verified':False}
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1]),indent=2))
