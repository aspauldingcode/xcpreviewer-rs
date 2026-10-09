"""Evidence-driven follow-ups using reviewed templates, without speculative code execution."""
from reloop.core import canonical_hash, load


def experiment(key, adapter, hypothesis, params, checks, priority=85, timeout=300):
    return {'id':key,'adapter':adapter,'hypothesis':hypothesis,'params':params,'checks':checks,
            'priority':priority,'timeout_seconds':timeout,'artifact_limit_mb':512,
            'depends_on':[],'resources':['local-re-controller']}


def plan(controller):
    latest=controller.status().get('runs',{})
    outcomes=[];proposals=[];seen=set()
    for key,run_id in sorted(latest.items()):
        manifest=load(controller.runs/run_id/'manifest.json',{})
        if not manifest.get('sealed') or not controller.verify(run_id)['valid']:
            outcomes.append({'experiment':key,'action':'quarantine','reason':'Evidence incomplete or changed'});continue
        spec=load(controller.runs/run_id/'experiment.json',{})
        result=load(controller.runs/run_id/'output/result.json',{})
        observed=result.get('observations',{}) if isinstance(result,dict) else {}
        failure=canonical_hash({'adapter':spec.get('adapter'),'params':spec.get('params'),
                                'execution':manifest.get('execution'),'error':result.get('error') if isinstance(result,dict) else 'invalid-result'})
        if manifest.get('execution')!='success':
            if failure in seen:continue
            seen.add(failure)
            outcomes.append({'experiment':key,'action':'diagnose-before-retry','fingerprint':failure,
                             'execution':manifest.get('execution'),'error':result.get('error') if isinstance(result,dict) else 'invalid result'})
            continue
        if spec.get('adapter')=='xcode_preview':
            if observed.get('wire_capture_complete') is False:
                outcomes.append({'experiment':key,'action':'recover-transport-boundary',
                                 'reason':'Rendered output/lifecycle is not complete correlated IPC evidence',
                                 'instrumented_processes':observed.get('instrumented_processes')})
            if spec.get('params',{}).get('variants',[0,1])==[0,1] and manifest.get('verdict')=='supports':
                proposals.append(experiment('canvas-repeat-control','xcode_preview',
                    'Two independent renders of unchanged owned baseline produce identical pixels under this pinned environment.',
                    {'variants':[0,0],'trace':False},[{'path':'rendered_variants','equals':2},
                     {'path':'pixels_identical','equals':True}],timeout=600))
        if spec.get('adapter')=='plist_corpus' and manifest.get('verdict')=='supports':
            seed=spec.get('params',{}).get('seed',1)+1
            proposals.append(experiment('plist-seed-%d'%seed,'plist_corpus',
                'Independent seeded owned dictionaries retain their values through all three decoders.',
                {'seed':seed,'cases':32},[{'path':'all_round_trips','equals':True},{'path':'cases','equals':32}]))
    # Templates are suggestions. The agent reviews and proposes them; no infinite background loop.
    proposals=[p for p in proposals if p['id'] not in latest][:4]
    return {'outcomes':outcomes,'proposals':proposals,'automatic_execution':False,
            'policy':'Choose one discriminating follow-up. Do not retry identical failures, renew budgets, or promote static names into wire semantics.'}
