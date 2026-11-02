"""Read captured method/graphics evidence; never reruns Xcode or proves pixel parity."""
from pathlib import Path
import json,argparse,hashlib
from PIL import Image,ImageStat

def verify(root):
 root=Path(root);rows=[json.loads(x) for x in (root/'attached/edit-events.jsonl').read_text().splitlines()]
 assert not any(x.get('message',{}).get('type')=='error' for x in rows)
 assert rows[-1]['source_restored'] and rows[-1]['stage']=='detached-no-target-termination'
 edited=next(x for x in rows if x.get('stage')=='source-color-edited');assert edited['sha256']=='80eb6505ab52d9121f38d6ddb3cdad2d450fe9994d537523a81e9bb9fd9b8bda'
 payloads=[(r,r['message']['payload']) for r in rows if r.get('message',{}).get('type')=='send'];ready=payloads[0][1]
 assert ready['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93' and ready['ui_uuid']=='0d87b0e2f4453035a9b6b1cf8230e015'
 stack=[];updates=0;assignments=0;threads=set()
 for r,v in payloads:
  event=v['event']
  if event=='preview-update-enter':assert r['time_ns']>edited['time_ns'];stack.append((event,v['id']));updates+=1;threads.add(v['thread'])
  elif event=='instance-assignment-helper-enter':assert stack and stack[-1][0]=='preview-update-enter' and v['caller_offset']=='0x3f978';stack.append((event,v['id']));assignments+=1;threads.add(v['thread'])
  elif event in ['preview-update-return','instance-assignment-helper-return']:
   expected='preview-update-enter' if event=='preview-update-return' else 'instance-assignment-helper-enter';assert stack.pop()==(expected,v['id'])
 assert not stack and updates>0 and assignments>0 and len(threads)==1
 repeat=[json.loads(x) for x in (root/'no-active-hooks/events.jsonl').read_text().splitlines()];assert repeat[-1]['source_restored'] and not repeat[0]['hooks']
 assert any(x.get('stage')=='source-color-edited' for x in repeat) and any(x.get('stage')=='source-color-restored' for x in repeat)
 data=json.loads((root/'assertions.json').read_text());roi=tuple(data['roi']);values={}
 for phase in ['baseline','attached_changed','attached_restored','repeat_changed','repeat_restored']:
  im=Image.open(root/(phase+'.jpg'));assert im.size==(1000,644);region=im.crop(roi);values[phase]=(hashlib.sha256(region.tobytes()).hexdigest(),ImageStat.Stat(region).mean)
 assert values['baseline'][0]==values['attached_restored'][0]==values['repeat_restored'][0]
 assert values['attached_changed'][0]==values['repeat_changed'][0] and values['baseline'][1][2]-values['attached_changed'][1][2]>80
 assert abs(values['baseline'][1][0]-values['attached_changed'][1][0])<3 and abs(values['baseline'][1][1]-values['attached_changed'][1][1])<3
 cleanup=json.loads((root/'cleanup.json').read_text());assert cleanup['source_sha256']=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef' and cleanup['controller_available']
 return {'preview_update_entries':updates,'instance_assignment_entries':assignments,'graphics_change_and_restore_observed':True,'same_process_no_active_hook_repeat':True,'interactive_state_or_pixel_parity_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);print(json.dumps(verify(p.parse_args().directory),indent=2))
