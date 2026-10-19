"""Conservative comparison of public process identity and supplied app inventory; no UI actions."""
def compare(expected,process,apps):
 if type(expected) is not dict or set(expected)!={'pid','identity','bundle_path'}:raise ValueError('expected shape')
 pid=expected['pid'];identity=expected['identity'];bundle=expected['bundle_path']
 if type(pid) is not int or not 1<pid<2**31 or type(identity) is not list or len(identity)!=3 or any(type(x) is not int or x<0 for x in identity[:2]) or identity[1]>=1000000 or type(identity[2]) is not str or not identity[2].startswith('/') or '\x00' in identity[2] or type(bundle) is not str or not bundle.startswith('/') or identity[2]!=bundle+'/Contents/MacOS/PreviewLab':raise ValueError('expected identity')
 if type(apps) is not list or len(apps)>16:raise ValueError('inventory bound')
 for app in apps:
  if type(app) is not dict or type(app.get('id')) is not str or ('isRunning' in app and type(app['isRunning']) is not bool):raise ValueError('app shape')
 result={'native_action_authorized':False,'process_identity_matches':False,'exact_path_running_app_candidates':0,'metadata_binding_available':False}
 if process is None:return {**result,'reason':'prior owned PID absent at this sample'}
 if type(process) is not dict or type(process.get('pid')) is not int or type(process.get('identity')) not in (list,tuple) or process.get('state') not in ('L','Z'):raise ValueError('process shape')
 observed=process['identity']
 if len(observed)!=3 or any(type(x) is not int or x<0 for x in observed[:2]) or observed[1]>=1000000 or type(observed[2]) is not str or not observed[2].startswith('/') or '\x00' in observed[2]:raise ValueError('observed identity shape')
 if process['pid']!=pid or list(process['identity'])!=identity:return {**result,'reason':'PID/birth/path mismatch; no identity reuse'}
 if process['state']!='L':return {**result,'reason':'owned process is not live'}
 result['process_identity_matches']=True
 matches=[a for a in apps if a['id']==bundle and a.get('isRunning') is True]
 result['exact_path_running_app_candidates']=len(matches)
 if len(matches)!=1:return {**result,'reason':'no unique exact-path running inventory entry; display name/bundle identifier alone is insufficient'}
 return {**result,'metadata_binding_available':True,'reason':'one current exact-path inventory entry and matching public live identity; window/view binding still unverified'}
