from pathlib import Path
import json,sys,tempfile,copy

def verify(s,selectors,clients):
 assert s['batch_messenger_field_offset']==32
 classes={x['class']:x for x in s['classes']};delegate=next(v for k,v in classes.items() if k.endswith('13SceneDelegate'))
 assert next(x for x in delegate['ivars'] if x['name']=='sceneMessenger')['offset']==32
 field=next(x for x in classes['PSScene']['ivars'] if x['name']=='_scene');assert field['offset']==8 and field['encoding']=='@"FBScene"'
 host=classes['FBScene'];client=classes['FBSScene'];assert host['superclass']==client['superclass']=='NSObject'
 assert all('FrontBoard.framework' in x['owner'] for x in host['methods']);assert all('FrontBoardServices.framework' in x['owner'] for x in client['methods'])
 forward=next(x for x in host['methods'] if x['selector']=='sendActions:toExtension:');assert forward['types']=='v32@0:8@16#24'
 ivars={x['name']:x['offset'] for x in host['ivars']};assert all(ivars[k]==v for k,v in {'_client':64,'_clientToken':56,'_legacy':218,'_active':219,'_invalidated':221}.items())
 refs={x['slot']:x['name'] for x in selectors['selectors']};assert selectors['uuid']=='77495253204f3556bc193f42134ab49c' and refs['0x29d997118']=='sendActions:toExtension:' and refs['0x29d996338']=='host:didReceiveActions:forExtension:'
 assert {x['class'] for x in clients}=={'FBLocalSynchronousSceneClientProvider','FBWorkspace'} and all(x['types']=='v40@0:8@16@24#32' for x in clients)
if __name__=='__main__':
 f=Path(sys.argv[1]);s=json.loads((f/'resolved.stdout').read_text());t=json.loads((f/'selectors.stdout').read_text());c=json.loads((f/'clients.stdout').read_text());verify(s,t,c);rejected=0
 for n in range(5):
  a,b,d=copy.deepcopy(s),copy.deepcopy(t),copy.deepcopy(c)
  if n==0:a['batch_messenger_field_offset']=24
  if n==1:next(x for v in a['classes'] if v['class']=='PSScene' for x in v['ivars'] if x['name']=='_scene')['encoding']='@"FBSScene"'
  if n==2:next(x for x in b['selectors'] if x['slot']=='0x29d997118')['name']='sendActions:completion:'
  if n==3:next(x for x in a['classes'] if x['class']=='FBScene')['methods'][0]['owner']='FrontBoardServices.framework'
  if n==4:d[0]['types']='v40@0:8@16@24@32'
  try:verify(a,b,d)
  except (AssertionError,KeyError,StopIteration):rejected+=1
 assert rejected==5
 print(json.dumps({'native_delegate_messenger_offset':32,'declared_host_class':'FBScene','registered_client_routes':2,'metadata_corruptions_rejected':5,'scene_constructors_invoked':0,'actions_sent':0,'live_canvas_route_observed':False}))
