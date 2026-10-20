from pathlib import Path
import json,copy,sys,importlib.util
spec=importlib.util.spec_from_file_location('old',Path(__file__).with_name('verify-lifetime.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
PHASES=['rights_before','rights_after','rights_late','rights_final']
def check(d,mode):
 old.check(d,mode)
 name=d['rights_before']['name'];assert isinstance(name,int)and name>0
 for phase in PHASES:
  s=d[phase];assert s['name']==name and s['header_name']==name;assert(s['header_bits']>>8)&255==21
  alive=mode!='delivered'and(phase in ['rights_before','rights_after']or(mode=='withheld'and phase=='rights_late'))
  assert s['type_status']==(0 if alive else 15)
  if alive:assert s['type']==131072
  for key in ['receive','send','send_once','dead_name']:
   assert s[key]['status']==(0 if alive else 15)
   if alive:assert s[key]['refs']==(1 if key=='receive'else 0)
  a=s['receive_status'];assert a['status']==(0 if alive else 15)
  if alive:
   assert a=={'status':0,'count':10,'send_once_rights':1,'send_rights_present':0,'queued_messages':0,'sequence_number':0}
  # Failed kernel query output buffers are deliberately not counted as evidence
  # of zero references, zero global send-once rights or port-object destruction.
 return name
if __name__=='__main__':
 folder=Path(sys.argv[1]);n=0;cases=[]
 for mode in ['delivered','withheld','late-after-invalidate']:
  d=json.load(open(folder/(mode+'.json')));check(d,mode)
  def mutated(bad):
   global n
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted corrupted right evidence')
  for phase in PHASES:
   for key in ['name','header_name','type_status']+(['type']if d[phase]['type_status']==0 else []):
    bad=copy.deepcopy(d);bad[phase][key]+=1;mutated(bad)
   bad=copy.deepcopy(d);bad[phase]['header_bits']^=256;mutated(bad)
   for key in ['receive','send','send_once','dead_name']:
    for field in ['status']+(['refs']if d[phase][key]['status']==0 else []):
     bad=copy.deepcopy(d);bad[phase][key][field]+=1;mutated(bad)
   bad=copy.deepcopy(d);bad[phase]['receive_status']['status']+=1;mutated(bad)
   if d[phase]['receive_status']['status']==0:
    for key in ['count','send_once_rights','send_rights_present','queued_messages','sequence_number']:
     bad=copy.deepcopy(d);bad[phase]['receive_status'][key]+=1;mutated(bad)
  phases=[]
  for phase in PHASES:
   s=d[phase];a=s['receive_status'];phases.append({'phase':phase,'type_status':s['type_status'],'receive_right_refs':s['receive']['refs']if s['receive']['status']==0 else None,'outstanding_send_once_rights':a['send_once_rights']if a['status']==0 else None})
  cases.append({'mode':mode,'same_exact_own_name_and_Mach2_header':True,'local_disposition_make_send_once':True,'phases':phases})
 print(json.dumps({'cases':cases,'right_receipt_mutations_rejected':n,'prior_lifetime_controls_preserved':True,'request_reply_bytes_verified':976,'all_native_resource_release_accounted':False,'target_operation_settlement':False,'global_port_object_destruction':False},indent=2))
