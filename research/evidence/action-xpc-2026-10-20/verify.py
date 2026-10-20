"""Independent owned-value expectations; never decode malformed native XPC."""
from pathlib import Path
import json,base64,plistlib,copy,sys

def verify(rows,endpoint):
 assert len(rows)==4
 total=0
 for i,r in enumerate(rows):
  assert r['mode']==i and bool(r['info_nil'])==(i==0) and bool(r['decoded_info_nil'])==(i==0)
  expected={'0':None,'1':None} if i<2 else {'0':'owned.message','1':{'count':7,'label':'owned'} if i==3 else 'owned.payload'}
  assert r['decoded_values']==expected
  tree=r['xpc'];assert tree['type']=='dictionary';root=tree['value'];assert set(root)==(set() if i==0 else {'i'})
  if not i:continue
  info=root['i'];assert info['type']=='dictionary';body=info['value'];assert body['bsx_class']=={'type':'string','value':'BSSettings'}
  assert set(body)==({'bsx_class'} if i==1 else {'bsx_class','objects'})
  if i==1:continue
  entries=body['objects'];assert entries['type']=='array' and len(entries['value'])==2
  for j,e in enumerate(entries['value']):
   assert e['type']=='array';p=e['value'];assert len(p)==3 and p[0]=={'type':'uint64','value':str(j)} and p[1]['type']=='dictionary'
   v=p[1]['value']
   if i==3 and j==1:
    assert p[2]=={'type':'int64','value':1} and set(v)=={'__BSXPCSecureClass','__BSXPCSecureValue'}
    assert v['__BSXPCSecureClass']=={'type':'string','value':'UVPropertyList'}
    inner=v['__BSXPCSecureValue'];assert inner['type']=='dictionary';inner=inner['value'];assert set(inner)=={'bsx_class','data'} and inner['bsx_class']=={'type':'string','value':'UVPropertyList'};d=inner['data'];b=base64.b64decode(d['base64'],validate=True);assert len(b)==d['bytes']==70;assert plistlib.loads(b)=={'count':7,'label':'owned'}
   else:
    assert p[2]=={'type':'int64','value':2} and set(v)=={'root'};d=v['root'];b=base64.b64decode(d['base64'],validate=True);assert b.startswith(b'bplist17') and len(b)==d['bytes']==66
   assert d['type']=='data';total+=len(b)
 assert total==268
 assert len(endpoint)==1;e=endpoint[0];assert e['mode']==4 and e['callback_arrived'] and e['callback_payload_matches'] and e['callback_on_owned_queue'] and e['callbacks']==1
 assert e['decoded_values']=={'0':'owned.message','1':'owned.payload'}
 assert e['xpc']['type']=='dictionary';root=e['xpc']['value'];assert set(root)=={'i','r'} and root['i']==rows[2]['xpc']['value']['i'];reply=root['r'];assert reply['type']=='dictionary';v=reply['value'];assert set(v)=={'bsar_aid','bsmpr_p','bsmpr_t'} and v['bsar_aid']['type']==v['bsmpr_t']['type']=='string' and v['bsmpr_p']=={'type':'mach send once right'}
 return {'native_no_responder_cases':4,'native_endpoint_case':1,'native_same_process_reply_callback':True,'expected_payload_and_queue':True,'native_data_bytes_preserved':268,'native_property_list_bytes_independently_decoded':70,'kernel_route_proven':False,'cross_process_canvas_transport':False}
if __name__=='__main__':
 f=Path(sys.argv[1]);rows=json.loads((f/'oracle.stdout').read_text());endpoint=json.loads((f/'endpoint.stdout').read_text());out=verify(rows,endpoint);rejected=0
 for kind in range(9):
  a=copy.deepcopy(rows);b=copy.deepcopy(endpoint)
  if kind==0:a[0]['decoded_info_nil']=False
  elif kind==1:a[1]['xpc']['value']['i']['value']['bsx_class']['value']='NSObject'
  elif kind==2:a[3]['xpc']['value']['i']['value']['objects']['value'][1]['value'][2]['value']=2
  elif kind==3:a[3]['decoded_values']['1']['count']=8
  elif kind==4:a[3]['xpc']['value']['i']['value']['objects']['value'][1]['value'][1]['value']['__BSXPCSecureValue']['value']['data']['bytes']=69
  elif kind==5:b[0]['callbacks']=2
  elif kind==6:b[0]['callback_payload_matches']=False
  elif kind==7:b[0]['callback_on_owned_queue']=False
  else:b[0]['xpc']['value']['r']['value']['bsmpr_p']['type']='mach send right'
  try:verify(a,b)
  except (AssertionError,ValueError,KeyError):rejected+=1
 assert rejected==9;out['receipt_mutations_rejected']=rejected;print(json.dumps(out))
