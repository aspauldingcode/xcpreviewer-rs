"""Validate this finite acquisition; no native command or agent is re-executed."""
import copy,datetime,hashlib,json,sys
from pathlib import Path

def need(value,message):
    if value is not True: raise ValueError(message)
def integer(x,v):return type(x) is int and x==v

def verify(p,report=None,cleanup=None,execution=None,plan=None):
    p=Path(p); r=json.loads((p/'result.json').read_text()) if report is None else report
    c=json.loads((p/'cleanup.json').read_text()) if cleanup is None else cleanup
    e=json.loads((p/'execution.json').read_text()) if execution is None else execution
    q=json.loads((p/'plan.json').read_text()) if plan is None else plan
    need(integer(e['exit'],0) and e['timeout'] is False,'terminal execution')
    need(integer(c['inspect_exit'],1) and c['removed'] is False and integer(c['remaining_exit'],0) and c['remaining']=='','automatic owned cleanup')
    deadline=datetime.datetime.fromisoformat(q['fixed_deadline_utc'].replace('Z','+00:00'))
    need(datetime.datetime.fromisoformat(c['completed_at'])<deadline and datetime.datetime.fromisoformat(e['finished_at'])<deadline,'fixed deadline')
    need(r['passed'] is True and r['model_tool_isolation_proven'] is False and r['handoff_approved'] is False,'scope promotion')
    need(type(r['uid']) is int and r['uid']>0 and type(r['gid']) is int,'unprivileged identity')
    need(r['cap_eff']=='0000000000000000' and r['no_new_privs']=='1' and r['interfaces']==['lo'],'reported process restrictions')
    need(r['host']['system']=='Linux' and r['host']['machine']=='aarch64','runtime scope')
    names=['allowed-input','allowed-output','input-write','root-write','unmounted-host-read','research-read','absolute-symlink-escape','relative-symlink-escape']
    need([x['case'] for x in r['rows']]==names and all(x['pass'] is True for x in r['rows']),'complete case set')
    for x in r['rows'][2:]:
        expected=30 if x['case'].endswith('write') else 2
        need(integer(x['errno'],expected) and integer(x['expected_errno'],expected),'failure discriminator')
    source=bytes([x for _ in range(4) for x in range(256)]); target=bytes([255-x for _ in range(4) for x in range(256)])
    need((p/'input-control.bin').read_bytes()==source and (p/'result.bin').read_bytes()==target,'all2048 independent file bytes')
    for row,data in zip(r['rows'],[source,target]):
        need(integer(row['bytes'],1024) and row['sha256']==hashlib.sha256(data).hexdigest(),'recorded bytes')
    args=q['args']; need(args[:3]==['docker','--context','colima'],'context')
    for flag,value in [('--pull','never'),('--network','none'),('--cap-drop','ALL'),('--security-opt','no-new-privileges'),('--name',q['name']),('--label','xcpreviewer.owner='+q['owner']),('--user',str(r['uid'])+':'+str(r['gid']))]:
        need(args.count(flag)==1 and args[args.index(flag)+1]==value,'command restriction '+flag)
    need('--read-only' in args and '--rm' in args and args.count('--mount')==3,'mount boundary')
    stage=q['stage']; mounts=[args[i+1] for i,x in enumerate(args) if x=='--mount']
    need(mounts==['type=bind,src='+stage+'/input,dst=/input,readonly','type=bind,src='+stage+'/output,dst=/work','type=bind,src='+stage+'/runner.py,dst=/runner.py,readonly'],'exact mount allowlist')
    need(q['image']=='sha256:4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109' and q['image'] in args,'image pin')
    before=set((p/'containers-before.txt').read_text().splitlines()); after=set((p/'containers-after.txt').read_text().splitlines());need(before<=after,'preexisting inventory')
    return {'complete_independent_file_bytes':2048,'cases':8,'owned_cleanup_verified':True,'container_process_only':True,'handoff_approved':False}

def controls(p):
    p=Path(p); accepted=verify(p); report=json.loads((p/'result.json').read_text());cleanup=json.loads((p/'cleanup.json').read_text());execution=json.loads((p/'execution.json').read_text()); plan=json.loads((p/'plan.json').read_text()); rejected=[]
    for label,field,change in [('missing-case','report',lambda x:x['rows'].pop()),('promoted-model-isolation','report',lambda x:x.update(model_tool_isolation_proven=True)),('false-exit','execution',lambda x:x.update(exit=False)),('cleanup-unobserved','cleanup',lambda x:x.update(remaining_exit=False)),('denial-not-enoent','report',lambda x:x['rows'][4].update(errno=13)),('extra-host-mount','plan',lambda x:x['args'].extend(['--mount','type=bind,src=/Users/8amps/xcpreviewer-rs,dst=/research']))]:
        values={'report':copy.deepcopy(report),'cleanup':copy.deepcopy(cleanup),'execution':copy.deepcopy(execution),'plan':copy.deepcopy(plan)}; change(values[field])
        try:verify(p,**values)
        except ValueError:rejected.append(label)
        else:raise ValueError('mutant accepted: '+label)
    return {'recorded':accepted,'rejected_mutants':rejected}
if __name__=='__main__':print(json.dumps(controls(sys.argv[1]),indent=2))
