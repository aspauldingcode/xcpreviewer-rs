"""Assert native provider/registry call-tree observations, not manual-render parity."""
import argparse,collections,json,tempfile
from pathlib import Path
from verify import verify
PROVIDERS=['collector','providers','registries']

def verify_providers(root):
    rows=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    ready=next(v['message']['payload'] for v in rows if v.get('message',{}).get('payload',{}).get('event')=='hooks-ready')
    assert ready['provider_targets']==[{'name':'collector','offset':'0x29d34'},{'name':'providers','offset':'0x3e4e0'},{'name':'registries','offset':'0x3eb94'}]
    assert ready['provider_call_cap']==1000
    filtered=[v for v in rows if v['stage']!='script' or not any(v['message'].get('payload',{}).get('event','').startswith(name+'-') for name in PROVIDERS)]
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in filtered));(p/'ui.json').write_bytes((root/'ui.json').read_bytes());base=verify(p,True)
    phase='startup';active={};stacks=collections.defaultdict(list);roots=collections.defaultdict(list);counts=collections.defaultdict(collections.Counter)
    for v in rows:
        if v['stage']=='phase':
            assert not active,'Phase boundary while an observed call remains open'
            phase=v['label'];continue
        if v['stage']!='script':continue
        e=v['message']['payload'];name=e['event']
        if name=='hooks-ready':continue
        assert name!='overflow' and phase in ['edit','restore']
        if name.endswith('-enter'):
            function=name[:-6];assert function in PROVIDERS+['preview-update','instance-assignment-helper'];assert e['id'] not in active
            thread=e['thread'];node={'function':function,'thread':thread,'children':[]};stack=stacks[thread]
            if stack:active[stack[-1]]['children'].append(node)
            else:roots[phase].append(node)
            active[e['id']]=node;stack.append(e['id']);counts[phase][function]+=1
        else:
            node=active.pop(e['id']);thread=node['thread'];assert name==node['function']+'-return'
            if 'thread' in e:assert e['thread']==thread
            assert stacks[thread].pop()==e['id']
    assert not active and all(not stack for stack in stacks.values())
    for phase in ['edit','restore']:
        assert len(roots[phase])>0
        for collector in roots[phase]:
            assert collector['function']=='collector'
            children=collector['children'];assert [c['function'] for c in children]==['providers','providers','registries','registries']
            assert all(c['thread']==collector['thread'] for c in children)
            assert not children[0]['children'] and not children[1]['children'] and not children[3]['children']
            updates=children[2]['children'];assert len(updates)==3
            for update in updates:
                assert update['function']=='preview-update' and len(update['children'])==1
                assert update['children'][0]['function']=='instance-assignment-helper' and not update['children'][0]['children']
    return {'base_controls':base,'native_call_counts':{p:dict(v) for p,v in counts.items()},'collector_tree_contract':'providers, providers, registries(three update/helper pairs), registries(empty); all selected calls matched by ID/thread','manual_interval_all_five_selected_probes':0,'manual_internal_route_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);print(json.dumps(verify_providers(p.parse_args().directory),indent=2))
