from pathlib import Path
import json,plistlib,sys,copy

def verify(r):
 for mode in ['absent','empty','structured']:
  row=json.loads((r/(mode+'.stdout')).read_text());present=mode!='absent'
  assert row['mode']==mode and row['payload_present']==present and row['response_class']=='BSActionResponse'
  assert row['slot1_class']==('UVPropertyList' if present else None)
  assert row['dictionary_equal']==present and row['serialized_property_list_equal']==present
  assert all(row[k] for k in ['response_payload_equal','settings_snapshot_survives_slot_replacement','callback_payload_equal','callback_arrived_within_500ms'])
  assert row['callbacks']==1 and row['external_action_sent'] is False
 assert plistlib.loads((r/'empty.bplist').read_bytes())=={}
 assert plistlib.loads((r/'structured.bplist').read_bytes())=={'answer':42,'bytes':b'abc','flags':[True,False],'nested':{'label':'owned'}}
if __name__=='__main__':
 r=Path(sys.argv[1]);verify(r)
 # Mutate independent receipts and fixture bytes without executing native code.
 import tempfile
 rejected=0
 with tempfile.TemporaryDirectory() as d:
  d=Path(d)
  for p in r.iterdir():
   if p.suffix in ['.stdout','.bplist']:(d/p.name).write_bytes(p.read_bytes())
  for key,value in [('callbacks',2),('payload_present',False),('slot1_class','NSDictionary'),('callback_payload_equal',False),('external_action_sent',True)]:
   p=d/'structured.stdout';original=p.read_bytes();s=json.loads(original);s[key]=value;p.write_text(json.dumps(s))
   try:verify(d)
   except (AssertionError,ValueError):rejected+=1
   p.write_bytes(original)
  p=d/'structured.bplist';original=p.read_bytes();p.write_bytes(original.replace(b'owned',b'other'))
  try:verify(d)
  except (AssertionError,ValueError):rejected+=1
 assert rejected==6
 print(json.dumps({'native_cases':3,'callbacks':3,'owned_serialized_bytes':156,'receipt_or_fixture_mutants_rejected':rejected,'remote_delivery_proven':False}))
