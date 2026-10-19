"""Independent admission of callback-model controls; no native authority."""
from pathlib import Path
import json,hashlib
CASES=['timeout_race_counterexample','pending_open_blocks_zero_cleanup','late_settlement_reconciles_without_deadline_success','rejecting_open_may_have_effect','no_dispatch_after_stop','stop_between_registration_and_dispatch','deadline_between_registration_and_dispatch','expiry_cannot_reverse_after_clock_regression','preexpiry_clock_regression_blocks_dispatch','deadline_boundary_is_expired','clock_failure_does_not_prevent_cleanup','clock_exception_stays_invalid_after_recovery','one_open_attempt','serial_operation_bound','expired_start_has_no_effect','close_receipt_owner_mismatch','zero_receipt_owner_mismatch','nonzero_windows_reject','boolean_zero_reject','close_pending_never_clean','zero_pending_never_clean','single_call_observation_failure_still_closes','no_unchanged_cleanup_retry','snapshot_cannot_clear_pending','immutable_owner_binding']
VARIANTS={'positive':('settlement.mjs',None),'before_dispatch':('settlement-before-dispatch-recheck.mjs','stop_between_registration_and_dispatch'),'before_clock':('settlement-before-clock-latch.mjs','expiry_cannot_reverse_after_clock_regression'),'missing_pending':('variants/missing_pending.mjs','pending_open_blocks_zero_cleanup'),'missing_dispatch_recheck':('variants/missing_dispatch_recheck.mjs','stop_between_registration_and_dispatch'),'late_is_timely':('variants/late_is_timely.mjs','late_settlement_reconciles_without_deadline_success'),'foreign_close':('variants/foreign_close.mjs','close_receipt_owner_mismatch'),'coerced_zero':('variants/coerced_zero.mjs','boolean_zero_reject'),'model_native_eligible':('variants/model_native_eligible.mjs','late_settlement_reconciles_without_deadline_success')}
def need(v):
 if not v:raise ValueError('Cleanup settlement model rejected')
def parsed(raw):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d);d[k]=v
  return d
 def constant(v):raise ValueError('Nonfinite JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
def admit(root):
 root=Path(root);v=parsed((root/'controls.json').read_text());need(v['native_UI_execution'] is False and v['real_provider_settlement_qualified'] is False)
 rows=v['records'];need(type(rows) is list and [x['variant'] for x in rows]==list(VARIANTS))
 for row in rows:
  source,failed=VARIANTS[row['variant']];need(row['source']==source and row['expected_failed_case']==failed)
  f=root/source;need(not f.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256'])
  need(type(row['syntax_exit']) is int and row['syntax_exit']==0 and type(row['exit']) is int and row['native_UI_execution'] is False)
  need(type(row['stdout']) is str and type(row['stderr']) is str)
  if failed is None:
   need(row['exit']==0 and row['stderr']=='');out=parsed(row['stdout']);need(out['native_UI_execution'] is False and out['native_eligible'] is False)
   need(type(out['cases']) is list and [x['case'] for x in out['cases']]==CASES and all(x['passed'] is True for x in out['cases']))
   need(all(type(out['environment'][k]) is str and out['environment'][k] for k in ['node','platform','arch']))
  else:need(row['exit']!=0 and failed in row['stderr'] and 'AssertionError' in row['stderr'])
 return {'model_cases':25,'retained_prototypes_rejected':2,'mutants_rejected':6,'native_UI_execution':False,'native_eligible':False,'real_provider_settlement_qualified':False,'native_cleanup_block_removed':False}
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent)))
