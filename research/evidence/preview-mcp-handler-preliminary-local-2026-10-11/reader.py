import base64,hashlib,json,subprocess
from pathlib import Path

def verify(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
 for name,meta in manifest['files'].items():
  p=folder/name;assert p.is_file() and p.stat().st_size==meta['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 saved=json.loads((folder/'result.json').read_text())
 for _ in range(2):
  r=subprocess.run([saved['node'],str(folder/'control.js'),str(folder/'preview_mcp.js'),str(folder/'preview_channel.js')],capture_output=True,timeout=8)
  assert r.returncode==0 and not r.stderr;assert json.loads(r.stdout)==saved['observed']
 d=saved['observed'];p=d['packets'];assert len(p)==16
 assert p[0]=={'jsonrpc':'2.0','id':0,'error':{'code':-32000,'message':'Initialization incomplete'}}
 assert p[1]=={'jsonrpc':'2.0','id':'init','result':{'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'owned-preview-handler','version':'0.1.0'}}}
 assert p[2]['error']['code']==-32000 and p[3] is None
 tools=p[4]['result']['tools'];assert [t['name'] for t in tools]==['preview_start','preview_poll','preview_status','preview_frame','preview_close']
 for t in tools:assert t['inputSchema']=={'type':'object','properties':{},'additionalProperties':False}
 assert json.loads(p[5]['result']['content'][0]['text'])=={'revision':1}
 expected=bytes((i*17+3)&255 for i in range(16384))
 for k in [6,8]:
  f=json.loads(p[k]['result']['content'][0]['text']);assert f['descriptor']=={'revision':1};assert base64.b64decode(f['allocationBase64'],validate=True)==expected
 assert p[7]['result']=={'content':[{'type':'text','text':'Preview operation failed'}],'isError':True}
 assert [p[k]['error']['code'] for k in [9,10,11,13]]==[-32602,-32602,-32601,-32600]
 assert p[12]=={'jsonrpc':'2.0','id':9,'result':{}} and p[14] is None
 assert json.loads(p[15]['result']['content'][0]['text'])=={'revision':1,'closed':True}
 assert len(d['malformed'])==9
 for v in d['malformed']:assert v=={'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Invalid request'}}
 assert d['limit']=={'jsonrpc':'2.0','id':256,'error':{'code':-32000,'message':'Session request limit'}} and d['ids']==256
 assert d['legacy']=={'accepted':0,'rejected':1,'cancelled':0,'writes':0,'closed':True,'reason':'invalid-request'} and d['legacyPackets']==[]
 return {'allocation_bytes':32768,'malformed_controls':9,'fresh_replays':2,'request_id_bound':256,'legacy_initialize_rejected':True}
