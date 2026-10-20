from pathlib import Path
import json,copy,sys
CLASS='FBSSceneIdentity'
def expected(mode):
 d={'bsx_class':{'type':'string','value':CLASS},'i':{'type':'string','value':'owned.scene.☃'if mode==3 else'owned.scene'}}
 if 1<=mode<=3:d['w']={'type':'string','value':'owned.workspace'}
 if mode>=2:d['iw']={'type':'string','value':'owned.internal'}
 return {'type':'dictionary','value':{'identity':{'type':'dictionary','value':d}}}
def check(rows):
 assert len(rows)==5
 for mode,row in enumerate(rows):
  assert row['mode']==mode and row['native_decode_fields_equal']is True and row['independent_expected_dictionary_equal']is True
  assert row['xpc']==expected(mode)
  fields={'identifier':'owned.scene.☃'if mode==3 else'owned.scene','workspaceIdentifier':'owned.workspace'if 1<=mode<=3 else None,'internalWorkspaceIdentifier':None if mode==0 else'owned.workspace'if mode==1 else'owned.internal'}
  assert row['fields']==fields
 return True
def verify(path):
 rows=json.loads(path.read_text());check(rows);rejected=0
 for case in range(8):
  bad=copy.deepcopy(rows)
  if case==0:bad[0]['xpc']['value']['identity']['value']['bsx_class']['value']='Wrong'
  elif case==1:bad[1]['xpc']['value']['identity']['value']['iw']={'type':'string','value':'owned.workspace'}
  elif case==2:bad[1]['fields']['internalWorkspaceIdentifier']=None
  elif case==3:bad[4]['fields']['workspaceIdentifier']='owned.internal'
  elif case==4:bad[3]['xpc']['value']['identity']['value']['i']['value']='owned.scene.?'
  elif case==5:bad[2]['xpc']['value']['identity']['value'].pop('iw')
  elif case==6:bad[0]['native_decode_fields_equal']=False
  else:bad[2]['xpc']['value']['identity']['value']['w']['type']='data'
  try:check(bad)
  except AssertionError:rejected+=1
  else:raise AssertionError('accepted identity mutation')
 n=sum(len(v['value'].encode('utf8'))for row in rows for v in row['xpc']['value']['identity']['value'].values())
 return {'native_cases':5,'native_independent_expected_decode_cases':5,'receipt_mutations_rejected':rejected,'owned_value_utf8_bytes_compared':n,'class':CLASS,'keys':['bsx_class','i','w','iw'],'internal_getter_falls_back_to_workspace':True,'raw_absence_preserved':True,'internal_without_workspace_native_supported':True,'scope':'Typed BSXPCCoder identity envelope; not service invocation/Mach serialization or Canvas routing'}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
