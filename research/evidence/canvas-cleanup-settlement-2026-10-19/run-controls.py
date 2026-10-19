"""Bounded offline Node controls; injected callbacks, no native UI APIs."""
from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).resolve().parent;s=(p/'settlement.mjs').read_text();variants=p/'variants';variants.mkdir(exist_ok=True)
specs=[('missing_pending',"if(pending.size!==0)return",'if(false)return','pending_open_blocks_zero_cleanup'),('missing_dispatch_recheck',"if(terminal||now()>=deadline)throw Error('terminal before dispatch');",'', 'stop_between_registration_and_dispatch'),('late_is_timely','!clockInvalid&&!expired&&t<deadline','true','late_settlement_reconciles_without_deadline_success'),('foreign_close',"matches(closed?.binding)",'true','close_receipt_owner_mismatch'),('coerced_zero',"!Number.isInteger(zero?.count)||zero.count!==0","zero.count!=0",'boolean_zero_reject'),('model_native_eligible','native_eligible:false','native_eligible:true','late_settlement_reconciles_without_deadline_success')]
candidates=[('positive',p/'settlement.mjs',None),('before_dispatch',p/'settlement-before-dispatch-recheck.mjs','stop_between_registration_and_dispatch'),('before_clock',p/'settlement-before-clock-latch.mjs','expiry_cannot_reverse_after_clock_regression')]
for name,old,new,expected in specs:
 if old not in s:raise ValueError(name)
 f=variants/(name+'.mjs');f.write_text(s.replace(old,new));candidates.append((name,f,expected))
records=[]
for name,f,expected in candidates:
 syntax=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=5)
 if syntax.returncode:raise ValueError('Invalid variant syntax')
 q=subprocess.run(['node',str(p/'test-settlement.mjs'),str(f)],capture_output=True,text=True,timeout=5)
 row={'variant':name,'source':str(f.relative_to(p)),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'syntax_exit':syntax.returncode,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'expected_failed_case':expected,'native_UI_execution':False}
 if expected is None:
  if q.returncode:raise ValueError(q.stderr)
 else:
  if q.returncode==0 or expected not in q.stderr or 'AssertionError' not in q.stderr:raise ValueError('Non-discriminating failure: '+name+' '+q.stderr)
 records.append(row)
(p/'controls.json').write_text(json.dumps({'records':records,'native_UI_execution':False,'real_provider_settlement_qualified':False},indent=2)+'\n')
print(json.dumps({'positive_cases':len(json.loads(records[0]['stdout'])['cases']),'retained_prototypes_rejected':2,'mutants_rejected':len(specs),'native_UI_execution':False}))
