"""Synthetic provider-evidence corruptions; no native execution."""
import copy,json,tempfile
from pathlib import Path
from verify_providers import verify_providers
source=Path(__file__).resolve().parents[3]/'research/evidence/canvas-runtime-provider-refresh-2026-11-03'
rows=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()];ui=json.loads((source/'ui.json').read_text());results=[]
for case in ['wrong-provider-offset','missing-provider-return','wrong-return-thread','wrong-provider-order','overflow','manual-provider-entry','missing-detach','refresh-action-failed']:
    e=copy.deepcopy(rows);u=copy.deepcopy(ui)
    def payload(event):return next(v['message']['payload'] for v in e if v.get('message',{}).get('payload',{}).get('event')==event)
    if case=='wrong-provider-offset':payload('hooks-ready')['provider_targets'][0]['offset']='0x0'
    elif case=='missing-provider-return':e.pop(next(i for i,v in enumerate(e) if v.get('message',{}).get('payload',{}).get('event')=='providers-return'))
    elif case=='wrong-return-thread':payload('providers-return')['thread']+=1
    elif case=='wrong-provider-order':
        identity=payload('providers-enter')['id']
        for v in e:
            p=v.get('message',{}).get('payload',{})
            if p.get('id')==identity:p['event']=p['event'].replace('providers-','registries-')
    elif case=='overflow':payload('collector-enter')['event']='overflow'
    elif case=='manual-provider-entry':
        index=next(i for i,v in enumerate(e) if v['stage']=='phase' and v['label']=='refresh-start');fake=copy.deepcopy(next(v for v in e if v.get('message',{}).get('payload',{}).get('event')=='collector-enter'));fake['time_ns']=e[index]['time_ns']+1;e.insert(index+1,fake)
    elif case=='missing-detach':e=[v for v in e if v['stage']!='session-detached']
    elif case=='refresh-action-failed':next(v for v in u if v['kind']=='action')['data']['ok']=False
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in e));(p/'ui.json').write_text(json.dumps(u))
        try:verify_providers(p)
        except (AssertionError,KeyError,IndexError,StopIteration):results.append({'case':case,'rejected':True})
        else:raise AssertionError('Accepted corruption: '+case)
print(json.dumps({'kind':'synthetic-provider-reader-controls','results':results},indent=2))
