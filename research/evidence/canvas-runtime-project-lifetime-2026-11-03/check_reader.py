"""Synthetic corruptions of retained evidence; no native execution here."""
import copy,json,tempfile,shutil
from pathlib import Path
from verify import verify
source=Path(__file__).resolve().parents[3]/'research/evidence/canvas-runtime-project-lifetime-2026-11-03'
u=json.loads((source/'ui.json').read_text());e=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()]
cases=['close-action-failed','wrong-project','no-reopen','final-unpinned','post-close-nil','wrong-image','unpaired-callback','cleanup-missing'];results=[]
for case in cases:
    ui=copy.deepcopy(u);rows=copy.deepcopy(e)
    if case=='close-action-failed':next(v for v in ui if v['kind']=='action' and v['args'].get('menu')=='File>Close Project')['data']['ok']=False
    elif case=='wrong-project':next(v for v in ui if v.get('label')=='open-panel')['data']['where']='unowned'
    elif case=='no-reopen':next(v for v in ui if v.get('label')=='reopened')['data']['ok']=False
    elif case=='final-unpinned':next(v for v in ui if v.get('label')=='final')['data']['pin_identifier']='pin'
    elif case=='post-close-nil':next(v for v in rows if v.get('message',{}).get('payload',{}).get('label')=='after-close')['message']['payload']['objects'][0]['weak_alive_at_load']=False
    elif case=='wrong-image':next(v for v in rows if v.get('message',{}).get('payload',{}).get('event')=='hooks-ready')['message']['payload']['uuid']='wrong'
    elif case=='unpaired-callback':rows=[v for v in rows if not(v.get('message',{}).get('payload',{}).get('event')=='method-return' and v['message']['payload']['call_id']==1)]
    elif case=='cleanup-missing':rows=[v for v in rows if v.get('message',{}).get('payload',{}).get('event')!='cleanup-done']
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);shutil.copyfile(source/'postflight.json',p/'postflight.json');(p/'ui.json').write_text(json.dumps(ui));(p/'events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in rows))
        try:verify(p)
        except (AssertionError,StopIteration,KeyError):results.append({'case':case,'rejected':True})
        else:raise AssertionError('Accepted corrupt evidence: '+case)
print(json.dumps({'kind':'synthetic-evidence-reader-controls','results':results},indent=2))
