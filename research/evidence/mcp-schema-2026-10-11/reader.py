import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[3]
def messages(handler,channel):
 rows=[p for p in handler['packets']+handler['malformed']+[handler['limit']] if p is not None]
 for c in channel['controls']:rows+=c['packets']
 return rows

def verify(folder):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
 for n,r in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=folder/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 provenance=json.loads((folder/'source-provenance.json').read_text());assert len(provenance['commit'])==40 and provenance['protocol']=='2025-11-25'
 for name,row in provenance['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==row['sha256'] and '/'+provenance['commit']+'/' in row['url']
 schema=json.loads((folder/'schema.json').read_text());Draft202012Validator.check_schema(schema)
 def validator(name):return Draft202012Validator({'$schema':schema['$schema'],'$defs':schema['$defs'],'$ref':'#/$defs/'+name})
 before=json.loads((folder/'before.json').read_text());after=json.loads((folder/'after.json').read_text());failures=[]
 for i,p in enumerate(messages(**before)):
  errors=list(validator('JSONRPCMessage').iter_errors(p))
  if errors:failures.append({'index':i,'packet':p,'errors':[e.message for e in errors]})
 assert len(failures)==7 and failures==json.loads((folder/'failures.json').read_text()) and all(f['packet']['id'] is None for f in failures)
 normalized=copy.deepcopy(before)
 for p in messages(**normalized):
  if p.get('id','absent') is None:p.pop('id')
 assert normalized==after and len(messages(**after))==36
 for p in messages(**after):validator('JSONRPCMessage').validate(p)
 hp=after['handler']['packets'];validator('InitializeResult').validate(hp[1]['result'])
 for i in [4,17]:validator('ListToolsResult').validate(hp[i]['result'])
 for i in [5,6,7,8,15]:validator('CallToolResult').validate(hp[i]['result'])
 for t in hp[4]['result']['tools']:
  Draft202012Validator.check_schema(t['inputSchema']);v=Draft202012Validator(t['inputSchema']);v.validate({});assert list(v.iter_errors({'unsafe':True}))
 cp=after['channel']['controls'][0]['packets'];validator('InitializeResult').validate(cp[0]['result']);validator('ListToolsResult').validate(cp[1]['result']);validator('CallToolResult').validate(cp[2]['result'])
 meta=json.loads((folder/'provenance.json').read_text());assert meta['invalid_before']==7 and meta['validated_after']==36
 assert hashlib.sha256(Path(meta['node']).read_bytes()).hexdigest()==meta['node_sha256']
 for kind,arg in [('handler','preview_channel.js'),('channel','mcp_channel.js')]:
  r=subprocess.run([meta['node'],str(folder/(kind+'-control.js')),str(folder/'preview_mcp.js'),str(folder/arg)],capture_output=True,timeout=8);assert r.returncode==0 and not r.stderr and json.loads(r.stdout)==after[kind]
 native=ROOT/'research/evidence/mcp-process-2026-10-11';assert hashlib.sha256((native/'manifest.json').read_bytes()).hexdigest()=='700c6bfe00763d9a5f54f450acc70444416755838185922e6c4deda87a71401e'
 count=0
 for row in json.loads((native/'process/result.json').read_text())['records']:
  for p in row['packets']:
   validator('JSONRPCMessage').validate(p);count+=1
   if p['id']==1:validator('InitializeResult').validate(p['result'])
   elif row['mode']=='edits' and p['id']==2:validator('ListToolsResult').validate(p['result'])
   elif row['mode']=='edits':validator('CallToolResult').validate(p['result'])
 assert count==16
 spec=importlib.util.spec_from_file_location('native_mcp_reader',Path(__file__).with_name('verify_mcp_process.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);facts=r.verify(native);assert facts['complete_bytes']==65536
 return dict(invalid_before=7,validated_owned=36,validated_native=16,complete_native_bytes=65536,sdk_interoperability=False)
