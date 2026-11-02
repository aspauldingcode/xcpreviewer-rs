"""Verify retained title-refresh artifacts; this does not execute native Xcode."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image

def verify(r):
 o=json.loads((r/'observations.json').read_text())
 assert o['source_restored_sha256']=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
 assert o['controller_available'] and not o['active_hooks']
 assert not o['input_delivery_qualified'] and not o['interactive_state_preservation_verified']
 events=[json.loads(x) for x in (r/'title-session/events.jsonl').read_text().splitlines()]
 stages=[e['stage'] for e in events]
 assert stages==['capture-ready','source-edit-begin','source-title-edited','source-title-restored','session-ended-no-target-termination'],stages
 assert events[-1]['source_restored']
 source=(r/'title-session/source-before.swift').read_bytes()
 assert hashlib.sha256(source).hexdigest()==o['source_restored_sha256']
 edited=source.replace(b'Text("Canvas baseline")',b'Text("Runtime state edit")')
 assert edited!=source and hashlib.sha256(edited).hexdigest()==events[2]['sha256']
 names=['baseline','after-increment','after-second-increment','title-edited','title-restored']
 ims=[Image.open(r/(n+'.png')).convert('RGB') for n in names]
 assert all(im.size==(2802,1804) for im in ims)
 title=lambda im:im.crop((2050,885,2450,950)).tobytes()
 count=lambda im: {i for i,rgb in enumerate(im.crop((2180,965,2320,1005)).getdata()) if max(rgb)<60}
 assert title(ims[0])!=title(ims[3]),'no preview title change'
 assert title(ims[0])==title(ims[4]),'preview title did not restore'
 base=count(ims[0]); similarities=[len(base & count(im))/len(base | count(im)) for im in ims]
 assert min(similarities)>.98,'count glyph mask changed; requalify manual observation'
 return {'artifact_assertions':'passed','native_execution_rerun':False,'input_delivery_qualified':False,'state_preservation_verified':False,'count_glyph_mask_iou':similarities}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);a=p.parse_args();print(json.dumps(verify(a.evidence),indent=2))
