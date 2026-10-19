"""Owned Unix-socket transport controls using frozen, unchanged source definitions."""
from pathlib import Path
import ast,datetime,hashlib,json,os,signal,socket,stat,subprocess,sys,tempfile,threading,time,types
P=Path(__file__).resolve().parent
signal.alarm(12)
def need(v):
 if not v:raise ValueError('Owned broker control failed')
def load(path,default=None):
 path=Path(path);return json.loads(path.read_text()) if path.exists() else default
def own_ps(args,**kw):
 need(args==['ps','-p',str(os.getpid()),'-o','lstart=','-o','command='])
 return subprocess.run(args,**kw)
source=(P/'xcodebridge.py').read_text();tree=ast.parse(source)
names={'identity','validate_request','BrokerClient','manage'}
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
need({n.name for n in nodes}==names)
namespace={'pathlib':__import__('pathlib'),'socket':socket,'stat':stat,'os':os,'json':json,'subprocess':types.SimpleNamespace(run=own_ps),'load':load,'DIRECTORY':Path('/private/tmp/unused-owned-broker-default'),'TOOLS':{'XcodeListWindows','XcodeGlob','XcodeRead','RenderPreview'},'LIMIT':8*1024*1024}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/'xcodebridge.py'),'exec'),namespace)
BrokerClient=namespace['BrokerClient'];manage=namespace['manage'];identity=namespace['identity']
records=[]
with tempfile.TemporaryDirectory(prefix='broker-control-',dir='/private/tmp') as tmp:
 root=Path(tmp);os.chmod(root,0o700)
 # An owned bound-but-not-listening endpoint is not a responsive server.
 d=root/'bound';d.mkdir(mode=0o700);s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);endpoint=d/'broker.sock';s.bind(str(endpoint));os.chmod(endpoint,0o600)
 (d/'record.json').write_text(json.dumps({'pid':os.getpid(),'identity':identity(os.getpid()),'initialized':True}));os.chmod(d/'record.json',0o600)
 try:
  metadata=manage('status',d);need(metadata['running'] is True and metadata['responsive'] is True)
  error=None
  try:BrokerClient(d,timeout=.05)
  except ConnectionRefusedError as e:error=type(e).__name__
  need(error=='ConnectionRefusedError')
  records.append({'case':'bound_endpoint_false_responsiveness','running':metadata['running'],'responsive_field':metadata['responsive'],'actual_status_response_verified':False,'client_error':error,'owned_pid':os.getpid(),'socket_cleanup_verified':False})
 finally:s.close();endpoint.unlink()
 need(not endpoint.exists());records[-1]['socket_cleanup_verified']=True
 # Caller timeout is causally before a separately authorized late server effect.
 d=root/'late';d.mkdir(mode=0o700);endpoint=d/'broker.sock';marker=d/'effect.bin';ready=threading.Event();permit=threading.Event();started=threading.Event();journal=[];errors=[];requests=[];server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
 server.bind(str(endpoint));os.chmod(endpoint,0o600);server.listen(2);server.settimeout(2)
 def work():
  try:
   ready.set()
   for index in range(2):
    conn,_=server.accept()
    with conn:
     conn.settimeout(2)
     with conn.makefile('rb') as stream:request=json.loads(stream.readline(4096))
     requests.append(request)
     if index==0:
      need(request=={'method':'status','params':{}});conn.sendall(json.dumps({'result':{'owned_mock':True,'pid':os.getpid()}}).encode()+b'\n')
     else:
      need(request=={'method':'tools/call','params':{'name':'XcodeListWindows','arguments':{}}});journal.append({'event':'server_received','at_ns':time.monotonic_ns()});started.set();need(permit.wait(2));marker.write_bytes(b'owned-late-effect\n');journal.append({'event':'server_effect','at_ns':time.monotonic_ns()})
      try:conn.sendall(b'{"result":{"owned_mock":true,"done":true}}\n')
      except BrokenPipeError:pass
  except BaseException as e:errors.append(type(e).__name__+':'+str(e))
  finally:server.close();endpoint.unlink(missing_ok=True)
 thread=threading.Thread(target=work,daemon=True);thread.start()
 try:
  need(ready.wait(1));client=BrokerClient(d,timeout=1);need(client.metadata=={'owned_mock':True,'pid':os.getpid()});client.timeout=.05;error=None
  try:client.request('tools/call',{'name':'XcodeListWindows','arguments':{}})
  except socket.timeout as e:error=type(e).__name__
  journal.append({'event':'caller_timeout','at_ns':time.monotonic_ns()});need(error==socket.timeout.__name__ and started.is_set());need(not marker.exists());journal.append({'event':'zero_before_terminal_server','at_ns':time.monotonic_ns()});permit.set();thread.join(2);need(not thread.is_alive() and not errors and marker.read_bytes()==b'owned-late-effect\n' and not endpoint.exists())
  records.append({'case':'caller_timeout_late_server_effect','owned_pid':os.getpid(),'caller_error':error,'status_response_verified':True,'requests':requests,'journal':journal,'zero_before_server_effect':True,'late_effect_hex':marker.read_bytes().hex(),'server_joined':True,'socket_cleanup_verified':True,'upstream_Apple_request':False})
 finally:permit.set();thread.join(2);need(not thread.is_alive());server.close();endpoint.unlink(missing_ok=True)
print(json.dumps({'records':records,'source_sha256':hashlib.sha256((P/'xcodebridge.py').read_bytes()).hexdigest(),'extracted_definitions':sorted(names),'scope':'Actual owned Unix socket behavior of frozen BrokerClient/manage definitions with explicit temporary endpoints; not upstream Apple/Xcode/UI execution','native_UI_execution':False,'native_cleanup_block_removed':False,'upstream_Apple_request':False,'environment':{'python':sys.version.split()[0],'platform':sys.platform}},indent=2))
