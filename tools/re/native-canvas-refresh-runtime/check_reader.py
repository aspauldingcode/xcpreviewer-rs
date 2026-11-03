"""Corrupt retained button-run evidence; synthetic checks, not native controls."""
import copy,json,tempfile
from pathlib import Path
from verify import verify,ORIGINAL
source=Path(__file__).resolve().parents[3]/'research/evidence/canvas-runtime-manual-refresh-2026-11-03/b'
rows=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()];ui=json.loads((source/'ui.json').read_text());result=[]
for case in ['wrong-image','missing-return','wrong-caller','unchanged-edit','not-paused','press-failed','pin-not-restored','manual-callback']:
    e=copy.deepcopy(rows);u=copy.deepcopy(ui)
    if case=='wrong-image':next(v for v in e if v.get('message',{}).get('payload',{}).get('event')=='hooks-ready')['message']['payload']['scenes_uuid']='wrong'
    elif case=='missing-return':
        index=next(i for i,v in enumerate(e) if v.get('message',{}).get('payload',{}).get('event')=='preview-update-return');e.pop(index)
    elif case=='wrong-caller':next(v for v in e if v.get('message',{}).get('payload',{}).get('event')=='instance-assignment-helper-enter')['message']['payload']['caller_offset']='0x0'
    elif case=='unchanged-edit':
        for v in e:
            if v['stage']=='phase' and v['label'] in ['edit','edit-settled']:v['source_sha256']=ORIGINAL
    elif case=='not-paused':next(v for v in u if v.get('label')=='baseline')['data']['canvas_paused']=False
    elif case=='press-failed':next(v for v in u if v['kind']=='action')['data']['ok']=False
    elif case=='pin-not-restored':next(v for v in u if v.get('label')=='restored')['data']['pin_identifier']='pin'
    elif case=='manual-callback':
        marker=next(i for i,v in enumerate(e) if v['stage']=='phase' and v['label']=='refresh-start');fake=copy.deepcopy(next(v for v in e if v.get('message',{}).get('payload',{}).get('event')=='preview-update-enter'));fake['time_ns']=e[marker]['time_ns']+1;e.insert(marker+1,fake)
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'ui.json').write_text(json.dumps(u));(p/'events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in e))
        try:verify(p,True)
        except (AssertionError,KeyError,StopIteration,IndexError):result.append({'case':case,'rejected':True})
        else:raise AssertionError('Accepted corrupted evidence: '+case)
print(json.dumps({'kind':'synthetic-reader-controls','results':result},indent=2))
