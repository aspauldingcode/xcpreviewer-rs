import sys,time,json,faulthandler
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
faulthandler.dump_traceback_later(8,repeat=True)
from reloop.core import Controller
from reloop.graphloop import inspect
c=Controller();original=c.verify
print(json.dumps({'event':'start','state':str(c.state)}),flush=True)
def verify(*a,**k):
 t=time.monotonic();print(json.dumps({'event':'verify_start','run':a[0]}),flush=True)
 v=original(*a,**k);print(json.dumps({'event':'verify_end','run':a[0],'seconds':time.monotonic()-t}),flush=True);return v
c.verify=verify
v=inspect(c);print(json.dumps({'event':'complete','candidates':v['candidates'],'execution_started':v['execution_started']}),flush=True)
