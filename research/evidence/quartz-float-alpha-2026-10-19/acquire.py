"""Validate guarded native acquisition separately from numerical comparison."""
import datetime
import json
from pathlib import Path
import compare as c
from phase_prerequisites import receipt, digest, parsed, require as need

def observed(root, historical=None):
    p=Path(root)
    pins=parsed((p/'approved-pins.json').read_text())
    for name,sha in pins.items():need(digest(p/name)==sha,'approved pin')
    source=digest(p/'probe.c');binary=parsed((p/'compile-record.json').read_text())['binary_sha256']
    need(type(binary) is str and len(binary)==64 and all(x in '0123456789abcdef' for x in binary),'binary hash')
    plan=parsed((p/'plan.json').read_text());execution_root=plan['execution_root']
    need(execution_root=='/private/tmp/quartz-float-alpha-20261019' and plan['deadline_utc']=='2026-10-19T16:48:00Z','execution plan')
    records={phase:receipt(p,phase,source,binary) for phase in ['compile','output-valid','fixture']}
    need(records['compile']['command']=='/usr/bin/xcrun' and records['compile']['args']==['clang','-framework','CoreGraphics','-framework','CoreFoundation',execution_root+'/probe.c','-o',execution_root+'/probe'],'compile command')
    need(records['fixture']['command']==execution_root+'/probe' and records['fixture']['args']==['--fixture',execution_root+'/owned-documents'],'fixture command')
    need(records['output-valid']['command']==execution_root+'/probe','output command')
    rea=parsed((p/'rea-identity.json').read_text())
    need(rea['owned_binary_sha256']==binary and rea['architecture']=='arm64' and rea['closed'] is True,'REA artifact')
    need(rea['server']['version']=='6.2.0' and rea['server']['command_path']=='/Users/8amps/xcpreviewer-rs/research/build/rea/node_modules/rea-agents/scripts/rea.mjs','REA server')
    times=[];deadline=datetime.datetime(2026,10,19,16,48,tzinfo=datetime.timezone.utc)
    for phase in ['compile','output-valid','fixture']:
        row=parsed((p/(phase+'-started.json')).read_text());t=datetime.datetime.fromisoformat(row['started_at'])
        need(row['phase']==phase and row['deadline_utc']=='2026-10-19T16:48:00Z' and t<deadline,'phase time');times.append(t)
    environment=parsed((p/'environment-before.json').read_text());before=datetime.datetime.fromisoformat(environment['observed_at'])
    need(environment['timing']=='before acquisition' and before<times[0],'environment chronology')
    complete=parsed((p/'completed.json').read_text());end=datetime.datetime.fromisoformat(complete['completed_at'])
    need(complete['deadline_utc']=='2026-10-19T16:48:00Z' and times==sorted(times) and times[-1]<end<deadline,'completion chronology')
    record=records['fixture']['record'];rows=[c.parsed(line) for line in record['stdout'].splitlines()]
    need(len(rows)==2 and type(rows[0]['pid']) is int and record['stderr']=='owned_tree_pid:'+str(rows[0]['pid'])+'\n','owned streams')
    need({f.name for f in (p/'owned-documents').iterdir()}=={'route%d-%s.raw'%(i,k) for i in range(2) for k in ['provider','readback']},'output inventory')
    old=c.anchored_old(historical if historical is not None else plan['historical_root'])
    result=c.compare(p/'owned-documents',rows,old)
    result['native_acquisition_qualified']=True
    result['scope']='owned public offscreen Float32 CoreGraphics acquisition; numerical relations and linear control reported separately'
    result['comparative_interpretation_qualified']=result['linear_identity_control']
    result['observed_process_drain']='scoped observed zero; unseen escapes excluded'
    return result

if __name__=='__main__':
    import sys
    print(json.dumps(observed(Path(__file__).resolve().parent,Path(sys.argv[1]) if len(sys.argv)>1 else None),sort_keys=True))
