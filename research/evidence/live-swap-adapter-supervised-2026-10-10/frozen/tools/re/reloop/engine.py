"""Schema-driven read access to the owned Ghidra program engine."""
import json
import pathlib
import urllib.parse
import urllib.request
from reloop.core import PROJECT_ROOT, atomic, digest, load
from reloop.ghidra import http, local_url
from reloop.worker import ghidra_config

READ_TOOLS = {
    'get_current_program_info', 'list_open_programs', 'search_functions',
    'list_functions_enhanced', 'decompile_function', 'get_xrefs_to',
    'get_xrefs_from', 'disassemble_function', 'get_function_by_address',
    'get_function_callers', 'get_function_callees', 'get_call_graph',
    'list_strings', 'search_strings', 'list_segments', 'list_imports',
    'list_exports', 'get_address_spaces', 'get_function_signature',
    'get_function_call_graph', 'analyze_dataflow', 'analysis_status',
}


def bases():
    _, _, config = ghidra_config()
    return (config.get('ghidra_engine_url', 'http://127.0.0.1:8089'),
            config.get('ghidra_vibe_url', 'http://127.0.0.1:8092'))


def health():
    engine, vibe = bases()
    result = http(vibe, 'vibe_health', {}, timeout=10)
    if not result.get('data', result).get('analysis', {}).get('ok'):
        raise RuntimeError('Ghidra program engine unhealthy')
    return engine


def catalog():
    schema = http(health(), 'mcp/schema')
    return {t['path'].lstrip('/'): t for t in schema['tools']
            if t.get('path', '').lstrip('/') in READ_TOOLS | {'load_program', 'create_function'}}


def dispatch(name, arguments, out=None):
    if name not in READ_TOOLS | {'load_program', 'create_function'}:
        raise ValueError('Unsupported analysis operation')
    engine = health()
    schema = http(engine, 'mcp/schema')
    tool = next((t for t in schema['tools'] if t.get('path') == '/' + name), None)
    if tool is None:
        raise ValueError('Operation not advertised by installed engine: ' + name)
    params = {p['name']: p for p in tool.get('params', [])}
    if set(arguments) - set(params):
        raise ValueError('Unexpected engine arguments')
    for key, spec in params.items():
        if spec.get('required') and key not in arguments:
            raise ValueError('Missing engine argument: ' + key)
    for key, value in arguments.items():
        typ = params[key]['type']
        if (typ == 'integer' and type(value) is not int or
                typ == 'boolean' and type(value) is not bool or
                typ == 'string' and not isinstance(value, str)):
            raise ValueError('Wrong engine argument type: ' + key)
        if key == 'limit' and not 1 <= value <= 200:
            raise ValueError('Engine page limit must be 1..200')
        if key == 'offset' and value < 0:
            raise ValueError('Negative offset')
        if key == 'timeout' and not 1 <= value <= 60:
            raise ValueError('Decompile timeout must be 1..60')
    if name in {'load_program', 'create_function'}:
        # Imports are restricted to the engine launched by this checkout.
        from reloop.services import process_identity
        record = load(PROJECT_ROOT / 'research/state/services/engine.json', {})
        if not record or process_identity(record['pid']) != record['identity']:
            raise RuntimeError('Program import requires repository-owned engine')
        if name == 'load_program':
            path = pathlib.Path(arguments['file']).resolve(strict=True)
            if not path.is_file():raise ValueError('Import requires a file')
        elif not arguments.get('program'):
            raise ValueError('Explicit program required for function preparation')
    elif 'program' in params and name != 'get_current_program_info' and not arguments.get('program'):
        raise ValueError('Explicit program identity required')
    query = {k: v for k, v in arguments.items() if params[k].get('source') == 'query'}
    body = {k: v for k, v in arguments.items() if params[k].get('source') == 'body'}
    suffix = '?' + urllib.parse.urlencode(query) if query else ''
    request = urllib.request.Request(local_url(engine) + '/' + name + suffix,
                                    data=json.dumps(body).encode() if tool['method'] == 'POST' else None,
                                    method=tool['method'], headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=150 if name == 'load_program' else 70) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise RuntimeError('Engine response exceeds 4 MiB; narrow query')
    text = raw.decode(errors='replace')
    try:
        result = json.loads(text)
    except ValueError:
        result = {'text': text}
    if isinstance(result, dict) and (result.get('error') or result.get('success') is False):
        raise RuntimeError(str(result))
    if isinstance(result, dict) and result.get('text', '').lower().startswith('error'):
        raise RuntimeError(result['text'])
    if out is not None:
        atomic(pathlib.Path(out) / (name + '.json'), {'operation': name, 'arguments': arguments, 'result': result})
    return result


def analyze(binary, query, out):
    """Join a known binary with bounded search, decompilation and references."""
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    target = pathlib.Path(binary).resolve(strict=True)
    atomic(out / 'engine-schema.json', catalog())
    loaded = dispatch('load_program', {'file': str(target)}, out)
    program = loaded.get('program')
    if not program:
        raise RuntimeError('Engine import did not identify program')
    info = dispatch('get_current_program_info', {'program': program}, out)
    if pathlib.Path(info.get('executable_path','')).resolve()!=target:
        raise RuntimeError('Engine program identity differs from requested binary')
    import subprocess
    symbols = subprocess.run(['nm', str(target)], capture_output=True, text=True, check=True, timeout=30).stdout
    prepared=[]
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==3 and parts[1].lower()=='t' and query in parts[2]:
            if len(prepared)>=20:break
            address='0x'+parts[0]
            dispatch('create_function', {'program':program,'address':address,'name':parts[2],'disassemble_first':True})
            prepared.append({'address':address,'symbol':parts[2]})
    atomic(out/'prepared-functions.json',prepared)
    functions = dispatch('search_functions', {'program': program, 'name_pattern': query, 'limit': 20}, out)
    atomic(out / 'identity.json', {'image_sha256': digest(target), 'program': program, 'program_info': info})
    return {'program': program, 'image_sha256': digest(target), 'functions': functions, 'prepared':prepared, 'program_info': info}
