from pathlib import Path
import json,copy,sys

def check(s,mode):
 early=mode=='early';assert s['mode']==mode and s['scheduled_seconds']==.08
 assert s['queue_class']=='BSServiceDispatchQueue' and s['queue_method_address']=='0x1a82eff28' and s['queue_method_owner']=='/System/Library/PrivateFrameworks/BoardServices.framework/Versions/A/BoardServices'
 assert s['callback_within_one_second'] and .07<=s['elapsed_seconds']<=1
 assert s['signal_before_queue_resume']==early and s['cleanup_winners_before_queue_resume']==int(early)
 assert s['capture_deallocations_before_queue_resume']==0 and s['capture_deallocations_after_timer_barrier']==1
 assert s['cleanup_winners_final']==1 and s['fallback_callbacks']==1
 assert s['scene_constructors_invoked']==0 and s['external_actions_sent']==0
if __name__=='__main__':
 f=Path(sys.argv[1]);rows={mode:json.loads((f/(mode+'.stdout')).read_text()) for mode in ['early','fallback']}
 for mode,s in rows.items():check(s,mode)
 rejected=0
 for mode,key,value in [('early','capture_deallocations_before_queue_resume',1),('early','capture_deallocations_after_timer_barrier',0),('early','cleanup_winners_final',2),('fallback','fallback_callbacks',0),('fallback','elapsed_seconds',.00008),('early','queue_class','BSServiceQueue'),('fallback','cleanup_winners_before_queue_resume',1)]:
  s=copy.deepcopy(rows[mode]);s[key]=value
  try:check(s,mode)
  except (AssertionError,KeyError):rejected+=1
 assert rejected==7
 print(json.dumps({'native_cases':2,'native_fallback_callbacks':2,'native_final_capture_deallocations':2,'capture_retained_after_early_signal':True,'receipt_mutants_rejected':7,'native_workspace_execution':False,'target_settlement_proven':False}))
