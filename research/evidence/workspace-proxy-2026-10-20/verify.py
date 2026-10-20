from pathlib import Path
import json,copy,hashlib,struct,sys
sha=lambda b:hashlib.sha256(b).hexdigest()
SELECTOR='sceneID:sendActions:toExtension:completion:'
ENCODINGS=['@"FBSSceneIdentity<__nonnull__>"','@"NSSet<__BSAction__>"','@"NSString"','@?<v@?@"NSError">']
def check(rows):
 assert len(rows)==2 and [r['factory']for r in rows]==['interface','invertedInterface']
 for i,r in enumerate(rows):
  assert r['class']=='BSServiceInterface' and r['identifier']=='com.apple.frontboard.workspace-service'
  found='server'if i else'client';other='client'if i else'server'
  assert r['roles'][found]['name']=='FBSWorkspaceServiceServerInterface' and r['roles'][other]['name']=='FBSWorkspaceServiceClientInterface'
  assert r['roles'][found]['target_method_found']==1 and r['roles'][other]['target_method_found']==0
  d=r['roles'][found]['details'];assert d['name']==SELECTOR and d['argument_count']==4
  assert d['encoding']=='Vv48@0:8'+ENCODINGS[0]+'16'+ENCODINGS[1]+'24'+ENCODINGS[2]+'32'+ENCODINGS[3]+'40'
  for j,arg in enumerate(d['arguments']):
   assert arg['encoding']==ENCODINGS[j] and arg['argument_index']==j and arg['is_object']==1 and arg['is_block']==(j==3)
  a=d['arguments'][3];assert a['block_return_encoding']=='v' and a['block_arguments']==[{'argument_index':0,'encoding':'@"NSError"','is_block':0,'is_object':1,'is_oneway':0}]
  assert d['return_value']=={'argument_index':9223372036854775807,'encoding':'Vv','is_block':0,'is_object':0,'is_oneway':1}
 assert rows[0]['roles']['client']['details']==rows[1]['roles']['server']['details']
 return True
def verify(path):
 rows=json.loads(path.read_text());check(rows);n=0
 for case in range(8):
  bad=copy.deepcopy(rows);r=bad[0];d=r['roles']['client']['details']
  if case==0:r['roles']['client'],r['roles']['server']=r['roles']['server'],r['roles']['client']
  elif case==1:d['arguments'][0]['encoding']='@"NSString"'
  elif case==2:d['arguments'][1]['encoding']='@"NSSet"'
  elif case==3:d['arguments'][2]['argument_index']=3
  elif case==4:d['arguments'][3]['block_arguments'][0]['encoding']='B'
  elif case==5:d['return_value']['is_oneway']=0
  elif case==6:r['identifier']='owned.wrong.service'
  else:d['argument_count']=3
  try:check(bad)
  except AssertionError:n+=1
  else:raise AssertionError('accepted contract mutation')
 return {'factories':2,'role_direction_mutations_rejected':n,'service_identifier':rows[0]['identifier'],'selector':SELECTOR,'normal_client_protocol':'FBSWorkspaceServiceServerInterface','inverted_server_protocol':'FBSWorkspaceServiceServerInterface','argument_encodings':ENCODINGS,'argument_indices':[0,1,2,3],'completion_argument_encoding':'@"NSError"','oneway_void':True,'wire_serialization_observed':False,'workspace_constructors_invoked':0,'service_connection_constructors_invoked':0,'scene_methods_invoked':0}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
