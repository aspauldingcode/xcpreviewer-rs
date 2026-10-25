from pathlib import Path
import plistlib,json,struct,subprocess
w=Path(__file__).parent
p=lambda kind,**fields:{'messageType':kind,'payload':fields}
cases=[('ping',p('ping')),('capabilities-absent',p('capabilities')),('capabilities-false',p('capabilities',isRunningInXTP=False)),('capabilities-invalid',p('capabilities',isRunningInXTP=2)),('purge-default',p('purge',workspaceID='owned\n🦀')),('purge-true',p('purge',workspaceID='',killAgents=1)),('cancel-wide',p('cancelUpdate',pid=23,contentIdentifier='owned',updateSeed=2**64-1)),('connect',p('connect',pid=23)),('stop',p('stop',pid=-1)),('kill',p('kill',pid=0)),('audit',p('connect',discriminant='auditToken',auditToken={'val':[0,1,2,3,4,0xffffffff,6,7]})),('forward',p('forward',pid=23,messageType='render',messagePayload={'blob':b'\x00\xff','unsigned':2**64-1}))]
for name,value in cases:
 value['payload']['__unique_service_message_identifier']='owned\n\0🦀';value['extra']='omitted'
 (w/(name+'.input.bplist')).write_bytes(plistlib.dumps(value,fmt=plistlib.FMT_BINARY))
 canonical={'messageType':value['messageType'],'payload':dict(value['payload'])}
 if name.startswith('capabilities'):
  if name in ['capabilities-absent','capabilities-invalid']:canonical['payload'].pop('isRunningInXTP',None)
 if name=='purge-default':canonical['payload']['killAgents']=False
 if name=='purge-true':canonical['payload']['killAgents']=True
 if name=='audit':canonical['payload']['pid']=-1
 if name=='forward':canonical['payload']['previewInterfaceOrientation']='portrait'
 (w/(name+'.expected.bplist')).write_bytes(plistlib.dumps(canonical,fmt=plistlib.FMT_BINARY))
(w/'cases.json').write_text(json.dumps([name for name,_ in cases])+'\n')
