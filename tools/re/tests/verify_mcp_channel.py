import base64,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def verify(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
 for n,m in manifest['files'].items():
  p=folder/n;assert p.stat().st_size==m['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
 saved=json.loads((folder/'result.json').read_text());provenance=json.loads((folder/'provenance.json').read_text())
 assert hashlib.sha256(Path(saved['node']).read_bytes()).hexdigest()==provenance['node_sha256']
 parent=ROOT/'research/evidence/preview-mcp-handler-2026-10-11/manifest.json';assert hashlib.sha256(parent.read_bytes()).hexdigest()==provenance['parent_manifest_sha256']
 for n,m in json.loads(parent.read_text())['files'].items():assert hashlib.sha256((parent.parent/n).read_bytes()).hexdigest()==m['sha256']
 assert json.loads((folder/'exit.json').read_text())=={'exit':0} and not (folder/'stderr.txt').read_bytes()
 for _ in range(2):
  r=subprocess.run([saved['node'],str(folder/'control.js'),str(folder/'preview_mcp.js'),str(folder/'mcp_channel.js')],capture_output=True,timeout=8);assert r.returncode==0 and not r.stderr and json.loads(r.stdout)==saved['observed']
 c=saved['observed']['controls'];assert [x['name'] for x in c]==['normal','cancel','eof','queue','size','utf8','chunk','deadline','backpressure','json-eof']
 expected=[(5,5,0,'input-ended'),(8,2,2,'input-ended'),(3,1,1,'input-ended'),(12,1,9,'queue-bound'),(0,0,0,'request-bound'),(0,0,0,'invalid-utf8'),(0,0,0,'chunk-bound'),(0,0,0,'channel-deadline'),(1,1,0,'output-failed'),(1,1,0,'input-ended')]
 for v,(received,writes,suppressed,reason) in zip(c,expected):
  assert v['result']==dict(received=received,writes=writes,suppressed=suppressed,closed=True,reason=reason) and v['final']==dict(closed=True,pending=False)
 p=c[0]['packets'];assert len(p)==5 and [x['id'] for x in p]==['init',0,'frame',None,1]
 assert p[0]['result']['protocolVersion']=='2025-11-25' and p[0]['result']['capabilities']=={'tools':{}}
 assert [x['name'] for x in p[1]['result']['tools']]==['preview_start','preview_poll','preview_status','preview_frame','preview_close']
 f=json.loads(p[2]['result']['content'][0]['text']);assert f['descriptor']=={'revision':1} and base64.b64decode(f['allocationBase64'],validate=True)==bytes((i*19+7)&255 for i in range(16384))
 assert p[3]==dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Parse error')) and p[4]==dict(jsonrpc='2.0',id=1,result={})
 assert len(c[1]['packets'])==2 and c[1]['packets'][1]==dict(jsonrpc='2.0',id=4,error=dict(code=-32600,message='Request ID reused'))
 for v in c[2:4]:assert len(v['packets'])==1 and v['packets'][0]['id']=='init'
 for v in c[4:9]:assert v['packets']==[]
 assert c[9]['packets']==[dict(jsonrpc='2.0',id=None,error=dict(code=-32600,message='Invalid request'))]
 return dict(controls=10,fresh_replays=2,synthetic_allocation_bytes=16384)
