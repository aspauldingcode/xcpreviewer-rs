"""Discover and health-gate the installed GhidraVibe MCP extension."""
import json
import urllib.parse
import urllib.request
from reloop.core import ROOT, PROJECT_ROOT, atomic, load


def local_url(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password:
        raise ValueError('Ghidra endpoints must be local HTTP addresses')
    return url.rstrip('/')


def http(base,path,body=None,timeout=5):
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(local_url(base)+'/'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=timeout) as response:
        raw=response.read(4*1024*1024).decode()
        try:return json.loads(raw)
        except ValueError:
            if path=='check_connection' and raw.startswith('Connection OK'):return {'ok':True,'text':raw}
            raise


def unpack(result):
    if 'content' not in result:return result
    for item in result['content']:
        if item.get('type')=='text':
            try:return json.loads(item['text'])
            except ValueError:continue
    return result


def call(tool,arguments,out):
    config=load(PROJECT_ROOT/'research/local-config.json',{})
    allowed=config.get('ghidra_read_tools',['vibe_health'])
    if tool not in allowed:raise ValueError('Tool must be reviewed in ghidra_read_tools before use: '+tool)
    command=config.get('ghidra_mcp_command',[])
    if command:
        from reloop.mcp_client import Client
        with (out/'bridge.stderr').open('wb') as stderr:
            client=None
            try:
                client=Client(command,stderr,timeout=30)
                schema=client.request('tools/list',{})
                atomic(out/'tool-schema.json',schema)
                if 'vibe_health' not in {t['name'] for t in schema.get('tools',[])}:raise RuntimeError('Bridge lacks vibe_health; select the GhidraVibe bridge')
                health=unpack(client.request('tools/call',{'name':'vibe_health','arguments':{}}))
                atomic(out/'health.json',health)
                if not health.get('data',health).get('analysis',{}).get('ok'):raise RuntimeError('Ghidra program engine unhealthy')
                if tool=='vibe_health':return {'engine_healthy':True,'tool_count':len(schema['tools'])}
                response=client.request('tools/call',{'name':tool,'arguments':arguments})
                atomic(out/'tool-result.json',response)
                if response.get('isError'):raise RuntimeError('Ghidra MCP tool returned an error')
                return {'engine_healthy':True,'tool_completed':True}
            finally:
                if client:client.close()
    base=config.get('ghidra_vibe_url','http://127.0.0.1:8092')
    schema=http(base,'mcp/schema');atomic(out/'tool-schema.json',schema)
    if 'vibe_health' not in {t['name'] for t in schema.get('tools',[])}:raise RuntimeError('Endpoint lacks vibe_health')
    health=http(base,'vibe_health',{},timeout=30);atomic(out/'health.json',health)
    if not health.get('data',health).get('analysis',{}).get('ok'):raise RuntimeError('Ghidra program engine unhealthy; see health.json')
    if tool=='vibe_health':return {'engine_healthy':True,'tool_count':len(schema['tools'])}
    if tool not in {t['name'] for t in schema['tools']}:raise ValueError('Tool not advertised by live server')
    response=http(base,tool,arguments,timeout=60)
    atomic(out/'tool-result.json',response)
    if response.get('ok') is False:raise RuntimeError('Ghidra tool failed; inspect tool-result.json')
    return {'engine_healthy':True,'tool_completed':True}
