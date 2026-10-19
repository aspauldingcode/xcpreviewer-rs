"""One bounded passive Xcode module-inventory injection; no replacements."""
import frida,threading,json,time,subprocess,signal
from pathlib import Path
p=Path('/private/tmp/direct-canvas-re-20261019');pid=60975
identity=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','comm='],capture_output=True,text=True,timeout=3).stdout.strip()
if not identity.endswith('/Applications/Xcode.app/Contents/MacOS/Xcode'):raise RuntimeError('Xcode identity changed')
result={'pid':pid,'identity':identity,'frida_version':frida.__version__,'attach_budget_seconds':5,'script_scope':'Only enumerate loaded preview modules; no interception, replacement, payload reading or Objective-C bridge assumed.','attached':False,'script_loaded':False,'messages':[]}
c=frida.Cancellable();timer=threading.Timer(5,c.cancel);timer.daemon=True;s=None;script=None;start=time.monotonic();signal.alarm(15)
try:
 timer.start()
 with c:s=frida.get_local_device().attach(pid)
 timer.cancel();result['attached']=True
 script=s.create_script("send({kind:'preview_modules',pid:Process.id,modules:Process.enumerateModules().filter(m=>/Preview/i.test(m.name)).map(m=>({name:m.name,path:m.path,base:m.base.toString(),size:m.size}))});")
 script.on('message',lambda message,data:result['messages'].append(message));script.load();result['script_loaded']=True
 time.sleep(.25)
except Exception as e:result['error']={'type':type(e).__name__,'message':str(e)}
finally:
 timer.cancel()
 if script:
  try:script.unload();result['script_unloaded']=True
  except Exception as e:result['unload_error']=str(e)
 if s:
  try:s.detach();result['detached']=True
  except Exception as e:result['detach_error']=str(e)
 result['elapsed_seconds']=time.monotonic()-start;(p/'frida-observe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
