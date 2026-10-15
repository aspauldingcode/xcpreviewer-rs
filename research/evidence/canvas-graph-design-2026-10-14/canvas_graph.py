"""Canvas research graph: evidence validation, role-aware planning and reviewed handoff.

This tool never launches native processes, agents, or product implementation.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONFIG='research/loop/canvas-graph.json'
ROLES={'investigator','evidence-verifier','spec-author','spec-reviewer','clean-implementer','delivery-verifier'}
GRADES={'static','owned-oracle','native-ui','native-correlated','public-spec','process-record'}


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe(root,name):
    p=Path(name)
    if p.is_absolute() or not p.parts or '..' in p.parts:raise ValueError('Unsafe relative path')
    root=Path(root).resolve();target=root/p
    if any((root/Path(*p.parts[:i])).is_symlink() for i in range(1,len(p.parts)+1)):raise ValueError('Symlink forbidden')
    target.resolve().relative_to(root)
    return target


def order(tasks):
    found={t['id']:t for t in tasks}
    if len(found)!=len(tasks):raise ValueError('Duplicate task')
    active=set();done=set();out=[]
    def visit(key):
        if key not in found:raise ValueError('Unknown task dependency')
        if key in active:raise ValueError('Task dependency cycle')
        if key in done:return
        active.add(key)
        for dep in found[key]['requires']:visit(dep)
        active.remove(key);done.add(key);out.append(key)
    for key in sorted(found):visit(key)
    return out


def validate(root,graph):
    if graph.get('schema_version',1)!=1:raise ValueError('Unsupported graph schema')
    ontology=read(safe(root,graph['ontology']));types=set(ontology['entity_types']);relations=ontology['relations']
    nodes={n['id']:n for n in graph['knowledge']['nodes']}
    if len(nodes)!=len(graph['knowledge']['nodes']):raise ValueError('Duplicate entity')
    fusion=set()
    for n in nodes.values():
        if n['type'] not in types:raise ValueError('Unknown entity type')
        key=(n['type'],n['semantic_key'],n['scope'],n['target_version'])
        if key in fusion:raise ValueError('Unfused duplicate within scope/version')
        fusion.add(key)
        if n['grade'] not in GRADES:raise ValueError('Unknown evidence grade')
        provenance=n['provenance'];p=safe(root,provenance['path'])
        if sha(p)!=provenance['sha256']:raise ValueError('Changed provenance: '+str(p))
        if not provenance['locator'] or not provenance['extracted_at'] or provenance['confidence'] not in {'observed','inferred','unknown'}:raise ValueError('Incomplete provenance')
        if n['type']=='Evidence' and n.get('sealed_manifest'):
            m=read(p)
            for name,row in m['files'].items():
                item=safe(p.parent,name)
                if item.stat().st_size!=row['bytes'] or sha(item)!=row['sha256']:raise ValueError('Evidence artifact mismatch')
            actual={str(q.relative_to(p.parent)) for q in p.parent.rglob('*') if q.is_file() and q!=p}
            if actual!=set(m['files']):raise ValueError('Incomplete evidence manifest')
    for edge in graph['knowledge']['edges']:
        spec=relations[edge['relation']];a=nodes[edge['from']];b=nodes[edge['to']]
        if a['type'] not in spec['domain'] or b['type'] not in spec['range']:raise ValueError('Relation domain/range mismatch')
        if edge['source'] not in nodes or nodes[edge['source']]['type']!='Evidence' or not edge['extracted_at'] or edge['confidence'] not in {'observed','inferred','unknown'}:raise ValueError('Edge provenance missing')
        if edge['relation'] in {'SUPPORTS','QUALIFIES'} and a['grade']!=b['grade']:raise ValueError('Evidence grade escalation forbidden')
    ids=set(order(graph['tasks']))
    for task in graph['tasks']:
        if task['role'] not in ROLES or task['grade_required'] not in GRADES:raise ValueError('Invalid task role/grade')
        if task['kind'] not in {'research','verification','specification','implementation','delivery'}:raise ValueError('Invalid task kind')
        if not task['acceptance_checks'] or not task['outputs'] or not task['issue_ids']:raise ValueError('Task contract missing')
        if task['kind']=='implementation' and task['role']!='clean-implementer':raise ValueError('Implementation requires clean context')
        for field in ['requires','acceptance_checks','outputs']:
            if len(task[field])!=len(set(task[field])):raise ValueError('Duplicate contract entry')
        budget=task.get('budget',{})
        for key,maximum in [('rounds',4),('native_jobs',2),('seconds_per_native_job',60),('artifact_bytes',1073741824)]:
            value=budget.get(key)
            if type(value) is not int or value<0 or value>maximum:raise ValueError('Missing or excessive task budget')
        if task['id'] in task['requires'] or any(x not in ids for x in task['requires']):raise ValueError('Invalid dependency')
    return {'valid':True,'entities':len(nodes),'relations':len(graph['knowledge']['edges']),'tasks':len(ids),'semantic_review_complete':False,'delivery_accepted':False}


def plan(root,graph,role='investigator'):
    validate(root,graph)
    if role not in ROLES:raise ValueError('Unknown planning role')
    # No node is completed from task status, GitHub closure, model confidence or file existence.
    attest=graph.get('attestations',{});accepted=set();rows=[]
    for key in order(graph['tasks']):
        task=next(t for t in graph['tasks'] if t['id']==key);block=[]
        record=attest.get(key)
        if record:
            report=read(safe(root,record['path']))
            if sha(safe(root,record['path']))!=record['sha256']:raise ValueError('Review changed')
            if (report.get('task')!=key or report.get('verdict')!='accepted' or report.get('reviewer_context')==report.get('producer_context') or not report.get('reviewer_context') or not report.get('producer_context')):raise ValueError('Independent review required')
            if set(report.get('checks',{}))!=set(task['acceptance_checks']) or not all(v is True for v in report['checks'].values()):raise ValueError('Acceptance checks incomplete')
            if report.get('grade')!=task['grade_required'] or report.get('scope')!=task['scope']:raise ValueError('Review scope/grade mismatch')
            if {a['path'] for a in report.get('artifacts',[])}!=set(task['outputs']):raise ValueError('Reviewed outputs do not match task contract')
            for artifact in report.get('artifacts',[]):
                if sha(safe(root,artifact['path']))!=artifact['sha256']:raise ValueError('Reviewed artifact changed')
            if not report.get('artifacts'):raise ValueError('Review artifacts required')
            if all(x in accepted for x in task['requires']):accepted.add(key)
        if key in accepted:state='complete'
        else:
            if task.get('external_prerequisite'):block.append(task['external_prerequisite'])
            block.extend('requires:'+x for x in task['requires'] if x not in accepted)
            if task['role']!=role:block.append('separate-context:'+task['role'])
            if task['kind']=='implementation':block.append('isolated-workspace-and-reviewed-handoff-required')
            state='blocked' if block else 'ready'
        rows.append({**task,'state':state,'blockers':block})
    rows.sort(key=lambda t:(t['state']!='ready',-t['priority'],t['id']))
    gates=lambda milestone:[t['id'] for t in graph['tasks'] if t.get('milestone_gate')==milestone]
    return {'role':role,'tasks':rows,'next_task':next((t['id'] for t in rows if t['state']=='ready'),None),'execution_started':False,'automatic_delegation':False,'milestone1_complete':bool(gates(1)) and all(k in accepted for k in gates(1)),'milestone2_complete':bool(gates(2)) and all(k in accepted for k in gates(2))}


def export_handoff(root,review_path,destination):
    """Allowlist only. Independent review is a recorded attestation, not sandbox proof."""
    review=read(safe(root,review_path))
    if review.get('verdict')!='approved' or not review.get('author_context') or not review.get('reviewer_context') or review['author_context']==review['reviewer_context']:raise ValueError('Independent handoff approval required')
    if review.get('behavior_only_reviewed') is not True or review.get('provenance_reviewed') is not True:raise ValueError('Behavior/provenance review required')
    files=review.get('files',[])
    if not files or len(files)>128:raise ValueError('Bounded nonempty handoff required')
    seen=set();total=0;admitted=[]
    for row in files:
        if row['kind'] not in {'behavior-spec','public-standard-reference','original-asset','licensed-asset','behavior-test'}:raise ValueError('Forbidden handoff kind')
        p=safe(root,row['path']);name=row['name']
        if name=='HANDOFF-MANIFEST.json' or any(part.startswith('.') for part in Path(name).parts):raise ValueError('Reserved handoff path')
        if name in seen:raise ValueError('Duplicate handoff name')
        safe(Path('/private/tmp/handoff-validation'),name);seen.add(name)
        if Path(name).suffix.lower() not in {'.md','.json','.txt','.png','.svg','.wav','.ttf','.otf'}:raise ValueError('Unreviewed handoff format')
        if sha(p)!=row['sha256']:raise ValueError('Changed reviewed file')
        total+=p.stat().st_size
        if total>16777216:raise ValueError('Handoff byte limit')
        if row['kind'] in {'original-asset','licensed-asset'} and not row.get('attribution'):raise ValueError('Asset attribution missing')
        if not row.get('public_provenance'):raise ValueError('Public provenance missing')
        admitted.append((p,name))
    dest=Path(destination)
    if dest.exists():raise ValueError('Destination must be new; never reuse research checkout')
    # Validate everything before writing; bundle contains no internal graph or review history.
    dest.parent.mkdir(parents=True,exist_ok=True);temp=Path(tempfile.mkdtemp(prefix='.handoff-',dir=dest.parent))
    try:
        for p,name in admitted:
            out=safe(temp,name);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
        (temp/'HANDOFF-MANIFEST.json').write_text(json.dumps({'files':[{k:v for k,v in row.items() if k not in {'path'}} for row in files],'warning':'Content approved by separate reviewer; recipient isolation must be enforced by external workspace/tool permissions.'},indent=2)+'\n')
        os.rename(temp,dest)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {'exported_files':len(admitted),'destination':str(dest),'runtime_isolation_enforced':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--graph',default=CONFIG)
    sub=p.add_subparsers(dest='command',required=True);sub.add_parser('validate');q=sub.add_parser('plan');q.add_argument('--role',default='investigator');q=sub.add_parser('handoff');q.add_argument('review');q.add_argument('destination')
    args=p.parse_args()
    if args.command=='handoff':
        from reloop.core import Controller
        with Controller(root=args.root).lock():result=export_handoff(args.root,args.review,args.destination)
    else:
        graph=read(safe(args.root,args.graph));result=validate(args.root,graph) if args.command=='validate' else plan(args.root,graph,args.role)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
