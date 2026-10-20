from pathlib import Path
import json,hashlib,copy,sys
HASHES=['eedfe3bd92a2ab09bdd1470e71ed00c096a3723b51c5e2ef643424c1f6a4bb20','9cc1aaeb96582c5600a2fbaa120d1732ae7e7fde681fcf001afc51a026609c0e']
def receipt(s):
 assert s['initial_signalled'] is False and s['first_signal'] is True and s['second_signal'] is False and s['final_signalled'] is True
 assert s['scene_constructors_invoked']==0 and s['external_actions_sent']==0
 assert len(s['concurrent_trials'])==16
 for row in s['concurrent_trials']:assert row['attempts']==8 and row['winners']==1 and row['signalled'] is True
if __name__=='__main__':
 f=Path(sys.argv[1]);s=json.loads((f/'oracle.stdout').read_text());receipt(s)
 for i,h in enumerate(HASHES):assert hashlib.sha256((f/('signal-%d.bin'%i)).read_bytes()).hexdigest()==h
 names={x['slot']:x['name'] for x in json.loads((f/'resolve.stdout').read_text())};assert names['0x29cdebf60']=='BSAtomicSignal' and names['0x29d997018']=='sceneID:sendActions:toExtension:completion:' and names['0x29d996bc0']=='performAfter:withBlock:' and names['0x29d9962f8']=='hasBeenSignalled'
 rejected=0
 for n in range(6):
  m=copy.deepcopy(s)
  if n==0:m['first_signal']=False
  if n==1:m['second_signal']=True
  if n==2:m['concurrent_trials'][0]['winners']=2
  if n==3:m['concurrent_trials'][0]['attempts']=7
  if n==4:m['external_actions_sent']=1
  if n==5:m['concurrent_trials'][0]['signalled']=False
  try:receipt(m)
  except (AssertionError,KeyError):rejected+=1
 assert rejected==6
 print(json.dumps({'native_sequential_cases':4,'native_races':16,'native_race_attempts':128,'native_race_winners':16,'receipt_mutants_rejected':6,'native_method_probe_bytes':64,'native_workspace_send_executed':False,'target_settlement_proven':False}))
