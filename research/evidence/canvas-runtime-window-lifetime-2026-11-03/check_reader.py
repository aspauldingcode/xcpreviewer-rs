"""Synthetic evidence corruptions; these are not native runtime controls."""
import copy, json, tempfile, shutil
from pathlib import Path
from verify import verify
source=Path(__file__).resolve().parents[3]/'research/evidence/canvas-runtime-window-lifetime-2026-11-03'
ui=json.loads((source/'ui.json').read_text());events=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()]

def mutate(case,u,e):
    if case=='pin-transition':next(v for v in u if v.get('label')=='unpinned' and v['kind']=='observe')['pin_identifier']='pin.fill'
    elif case=='close-original':[v.update(id=u[0]['windows'][0]['id']) for v in next(x for x in u if x['kind']=='inventory' and x['label']=='created')['windows']]
    elif case=='action-failed':next(v for v in u if v['kind']=='action')['data']['ok']=False
    elif case=='missing-final':e[:]=[v for v in e if v.get('message',{}).get('payload',{}).get('label')!='restored']
    elif case=='weak-nil':next(v for v in e if v.get('message',{}).get('payload',{}).get('label')=='after-close')['message']['payload']['objects'][0]['weak_alive_at_load']=False
    elif case=='wrong-image':next(v for v in e if v.get('message',{}).get('payload',{}).get('event')=='hooks-ready')['message']['payload']['uuid']='wrong'
    elif case=='unpaired-setter':e[:]=[v for v in e if not(v.get('message',{}).get('payload',{}).get('event')=='method-return' and v['message']['payload']['call_id']==1)]
    elif case=='cleanup-missing':e[:]=[v for v in e if v.get('message',{}).get('payload',{}).get('event')!='cleanup-done']

result=[]
for case in ['pin-transition','close-original','action-failed','missing-final','weak-nil','wrong-image','unpaired-setter','cleanup-missing']:
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);shutil.copyfile(source/'postflight.json',p/'postflight.json');u=copy.deepcopy(ui);e=copy.deepcopy(events);mutate(case,u,e)
        (p/'ui.json').write_text(json.dumps(u));(p/'events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in e))
        try:verify(p)
        except (AssertionError,StopIteration,KeyError):result.append({'case':case,'rejected':True})
        else:raise AssertionError('Accepted corrupt evidence: '+case)
print(json.dumps({'kind':'synthetic-reader-controls','cases':result},indent=2))
