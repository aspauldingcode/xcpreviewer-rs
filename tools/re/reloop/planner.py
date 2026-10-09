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
            if observed.get('fixture_content_nonblank') is False:
                outcomes.append({'experiment':key,'action':'diagnose-blank-owned-content',
                                 'reason':'Returned PNGs or changed window titles do not establish rendered SwiftUI fixture content.'})
            elif observed.get('fixture_content_nonblank') is not True:
                outcomes.append({'experiment':key,'action':'require-owned-content-check',
                                 'reason':'Legacy capture checks can accept chrome-only snapshots; content readiness remains unverified.'})
            if observed.get('wire_capture_complete') is False:
                outcomes.append({'experiment':key,'action':'recover-transport-boundary',
                                 'reason':'Rendered output/lifecycle is not complete correlated IPC evidence',
                                 'instrumented_processes':observed.get('instrumented_processes')})
            if observed.get('fixture_content_nonblank') is True and spec.get('params',{}).get('variants',[0,1])==[0,1] and manifest.get('verdict')=='supports':
                proposals.append(experiment('canvas-repeat-control','xcode_preview',
                    'Two independent renders of unchanged owned baseline produce identical pixels under this pinned environment.',
                    {'variants':[0,0],'trace':False},[{'path':'rendered_variants','equals':2},
                     {'path':'pixels_identical','equals':True},{'path':'fixture_content_nonblank','equals':True}],timeout=600))
        if spec.get('adapter')=='xcode_bridge_probe':
            responsive=observed.get('initialized') is True and observed.get('direct_call_completed') is True
            outcomes.append({'experiment':key,'action':'attempt-owned-canvas-capture' if responsive else 'inspect-xcode-permission-and-service-readiness',
                             'reason':'Read-only tool response permits a separate owned capture attempt; it does not establish pixels or IPC.' if responsive else
                                      'Initialization alone is insufficient. Inspect permission/service state and require a changed prerequisite before retrying the direct route.',
                             'direct_call_completed':observed.get('direct_call_completed'),
                             'error':observed.get('direct_call_error')})
        if spec.get('adapter')=='plist_corpus' and manifest.get('verdict')=='supports':
            seed=spec.get('params',{}).get('seed',1)+1
            proposals.append(experiment('plist-seed-%d'%seed,'plist_corpus',
                'Independent seeded owned dictionaries retain their values through all three decoders.',
                {'seed':seed,'cases':32},[{'path':'all_round_trips','equals':True},{'path':'cases','equals':32}]))
        if spec.get('adapter')=='xpc_corpus' and manifest.get('verdict')=='supports':
            proposals.append(experiment('xpc-malformed-envelope','xpc_negative',
                'Malformed owned XPC envelopes distinguish absent data, invalid data, extra keys and direct-data decoder behavior.',{},
                [{'path':'missing_data_returns_nil','equals':True},{'path':'wrong_type_returns_nil','equals':True},
                 {'path':'truncated_data_decodes_empty_dictionary','equals':True},{'path':'extra_key_preserves_values','equals':True}],timeout=120))
        if spec.get('adapter')=='xpc_negative' and observed.get('truncated_data_decodes_empty_dictionary') is True:
            outcomes.append({'experiment':key,'action':'model-default-empty-explicitly',
                'reason':'Present malformed data can become an empty dictionary; missing/wrong-type XPC data is a different path. Preserve direct-data controls.'})
            proposals.append(experiment('xpc-prefix-boundary','xpc_prefix',
                'Every prefix of the owned Unicode payload establishes the nil/default-empty/full-value boundary.',{},
                [{'path':'full_prefix_preserves_values','equals':True},{'path':'incomplete_prefixes_preserving_values','equals':0},
                 {'path':'helper_failures','equals':0},{'path':'minimal_failure_preserved','equals':True}],timeout=180))
        if spec.get('adapter')=='xpc_prefix' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'recover-live-transport-and-attachments',
                'reason':'Local dictionary/data behavior is established for owned fixtures; complete live IPC correlation and resource lifetimes remain missing.'})
        if spec.get('adapter')=='agent_discriminants' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'validate-strings-in-live-envelope',
                'reason':'Static String raw values do not establish actual envelope selection, ordering or numeric wire IDs.'})
        if spec.get('adapter')=='raw_coder' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'keep-raw-coder-contract-narrow',
                'reason':'Owned controls ignore supplied keys and requested classes. Do not infer generic keyed secure decoding from selector names.'})
        if spec.get('adapter')=='surface_corpus' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'recover-interprocess-surface-lifecycle',
                'reason':'Local IOSurface holder/reference behavior and CPU bytes do not establish cross-process transfer, GPU completion or canvas ownership.'})
        if spec.get('adapter')=='surface_ipc' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'account-failure-and-timeout-release' if spec.get('params',{}).get('exit_order')=='receiver' else 'recover-reuse-and-completion-contract',
                'reason':('Owned CPU Mach handoff survives receiver exit; local send-right counts and port-retained access after CF release are measured. Failure/timeout cleanup and final reclamation remain open. '
                          if spec.get('params',{}).get('exit_order')=='receiver' else 'Owned CPU Mach handoff survives sender exit. ')+
                         'Reuse/ordering, GPU completion, revocation and actual canvas XPC envelopes remain unmeasured.'})
        if spec.get('adapter')=='surface_failure' and manifest.get('verdict')=='supports':
            use_state=spec.get('params',{}).get('control')=='use_state'
            outcomes.append({'experiment':key,'action':'recover-generation-and-completion-ordering' if use_state else 'discriminate-final-reclamation-and-reuse',
                             'reason':('Global in-use differs from local explicit count and can be false while retained CF pixels remain readable. '
                                       if use_state else 'Owned closed-endpoint/import-error/completion-timeout controls check local rights and bytes. ')+
                                      'Final kernel reclamation, reuse ordering and live Canvas transport remain unmeasured.'})
        if spec.get('adapter')=='surface_reuse' and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'recover-native-completion-and-stale-generation-rules',
                             'reason':'Owned CPU reuse demonstrates mutable storage and coalesced rights; assigned fixture generations do not recover Canvas sequencing or acknowledgements.'})
        if spec.get('adapter')=='native_reference' and spec.get('params',{}).get('repeat_control') and manifest.get('verdict')=='supports':
            outcomes.append({'experiment':key,'action':'use-separate-renderer-oracle-for-portable-subset',
                             'reason':'ImageRenderer A/A and controlled A/B can support rendering comparisons; Canvas IPC and hot reload remain separate gates.'})
    # Templates are suggestions. The scheduled agent reviews and implements them; native execution remains bounded.
    queued={e['id'] for e in load(controller.root/'research/loop/campaign.json',{}).get('experiments',[])}
    outcomes.extend({'experiment':p['id'],'action':'run-reviewed-followup','reason':'Template already queued; do not propose a duplicate.'}
                    for p in proposals if p['id'] in queued and p['id'] not in latest)
    proposals=[p for p in proposals if p['id'] not in latest and p['id'] not in queued][:4]
    return {'outcomes':outcomes,'proposals':proposals,'automatic_execution':False,
            'policy':'Choose one discriminating follow-up. Do not retry identical failures, renew budgets, or promote static names into wire semantics.'}
