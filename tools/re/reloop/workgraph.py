"""Delivery DAG and separately eligible research; accepted experiments never close issues."""
from reloop.core import load


def topology(issues):
    ordered=[];active=set();done=set()
    def visit(key):
        if key not in issues:raise ValueError('Unknown delivery dependency: '+key)
        if key in active:raise ValueError('Delivery dependency cycle: '+key)
        if key in done:return
        active.add(key)
        deps=issues[key].get('depends_on_ids',[])
        if not isinstance(deps,list) or len(deps)!=len(set(deps)):raise ValueError('Invalid delivery dependencies')
        for dep in sorted(deps):visit(dep)
        active.remove(key);done.add(key);ordered.append(key)
    for key in sorted(issues):visit(key)
    return ordered


def build(controller,roadmap=None,policy=None,checkpoint=None):
    roadmap=roadmap or load(controller.root/'research/roadmap/github.json')
    policy=policy or load(controller.root/'research/loop/workgraph.json')
    checkpoint=checkpoint or load(controller.root/'research/loop/continuous.json')
    issues=roadmap['issues'];order=topology(issues)
    anchors={r['run_id']:r['manifest_sha256'] for r in checkpoint.get('recent_evidence',[])}
    verified={};quarantine=[]
    def evidence(rid):
        if rid in verified:return verified[rid]
        anchor=anchors.get(rid)
        if not anchor:verified[rid]=False;return False
        result=controller.verify(rid,anchor)
        manifest=load(controller.runs/rid/'manifest.json',{})
        verified[rid]=(result.get('valid') is True and result.get('external_anchor_matches') is True
                       and manifest.get('sealed') is True and manifest.get('execution')=='success' and manifest.get('verdict')=='supports')
        if not verified[rid]:quarantine.append(rid)
        return verified[rid]
    # Completion is an explicit reviewed issue acceptance attestation, not GitHub state or a count of experiments.
    attestations=policy.get('acceptance_attestations',{})
    if set(attestations)-set(issues):raise ValueError('Unknown acceptance issue')
    accepted={}
    for key in order:
        a=attestations.get(key,{})
        deps=issues[key]['depends_on_ids']
        runs=a.get('runs',[])
        accepted[key]=(a.get('contract_reviewed') is True and isinstance(a.get('coverage_path'),str)
                       and bool(a['coverage_path']) and bool(runs) and all(evidence(r) for r in runs)
                       and all(accepted[d] for d in deps))
        # Coverage must itself be a sealed artifact; a pathname by itself is insufficient.
        if accepted[key]:
            coverage=a['coverage_path']
            accepted[key]=any(any(x.get('path')==coverage for x in load(controller.runs/r/'manifest.json',{}).get('artifacts',[])) for r in runs)
    descendants={key:set() for key in issues}
    for key in reversed(order):
        for dep in issues[key]['depends_on_ids']:descendants[dep].update({key}|descendants[key])
    blocks={b['track']:b for b in checkpoint.get('blocked_tracks',[])}
    tasks=[];seen=set()
    for task in policy['research_tasks']:
        key=task['id'];issue=task['issue']
        if key in seen or issue not in issues:raise ValueError('Invalid research task identity')
        seen.add(key);refs=task.get('requires_runs',[])
        missing=[rid for rid in refs if not evidence(rid)]
        block=blocks.get(task.get('blocked_track'))
        completed=task.get('completion_runs',[])
        if completed and not isinstance(completed,list):raise ValueError('Invalid research completion')
        valid_completion=bool(completed) and all(evidence(rid) for rid in completed)
        if valid_completion:
            allowed=task.get('completion_experiment_ids',[key])
            valid_completion=all(load(controller.runs/rid/'experiment.json',{}).get('id') in allowed for rid in completed)
        state='complete' if valid_completion and not missing else ('blocked' if block else ('evidence-required' if missing else 'ready'))
        tasks.append({**task,'state':state,'missing_evidence':missing,'blocker':block,
                      'unlocks_delivery_nodes':sum(not accepted[k] for k in descendants[issue]),
                      'acceptance_dependencies_unmet':[d for d in issues[issue]['depends_on_ids'] if not accepted[d]]})
    tasks.sort(key=lambda t:(t['state']!='ready',-t['priority'],-t['unlocks_delivery_nodes'],t['id']))
    nodes=[{'id':k,'kind':'delivery','milestone':issues[k]['milestone'],'issue_url':issues[k]['url'],
            'acceptance_verified':accepted[k],'dependencies':issues[k]['depends_on_ids']} for k in order]
    nodes.extend({'id':t['id'],'kind':'research','state':t['state'],'scope':t['scope']} for t in tasks)
    edges=[{'from':d,'to':k,'kind':'acceptance-prerequisite'} for k in order for d in issues[k]['depends_on_ids']]
    edges.extend({'from':t['id'],'to':t['issue'],'kind':'research-assists'} for t in tasks)
    required=[k for k in order if issues[k]['milestone']==1]
    second=[k for k in order if issues[k]['milestone']==2]
    return {'milestone2_complete':bool(second) and all(accepted[k] for k in second),'all_milestones_complete':bool(required) and bool(second) and all(accepted[k] for k in required+second),'nodes':nodes,'edges':edges,'topological_delivery_order':order,'research_frontier':tasks,
            'next_task':next((t['id'] for t in tasks if t['state']=='ready'),None),'quarantined_runs':sorted(set(quarantine)),
            'milestone1_complete':bool(required) and all(accepted[k] for k in required),
            'unverified_milestone1': [k for k in required if not accepted[k]],
            'policy':'Research can advance before acceptance dependencies complete. Scoped owned/static results never automatically satisfy native runtime/transport or delivery acceptance.'}
