"""Bounded structural reader for sanitized Xcode diagnostics, not wire evidence."""
import hashlib
import re


def _tree(text):
    if len(text.encode('utf-8')) > 65536:
        raise ValueError('display-state report exceeds 64 KiB')
    lines = text.splitlines()
    if len(lines) > 2048:
        raise ValueError('too many report lines')
    root = []
    stack = [(None, root)]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line in (']', '}'):
            if len(stack) == 1 or stack[-1][0] != line:
                raise ValueError('unbalanced report')
            stack.pop()
            continue
        opening = re.fullmatch(r'(.+) ([\[{])', line)
        if opening:
            if len(stack) > 16:
                raise ValueError('excessive nesting')
            name, delimiter = opening.groups()
            children = []
            stack[-1][1].append((name, delimiter, children))
            stack.append((']' if delimiter == '[' else '}', children))
            continue
        scalar = re.fullmatch(r'([^:{}]+): ([^{}]+)', line)
        if not scalar:
            raise ValueError('unsupported report line')
        stack[-1][1].append((scalar[1], None, scalar[2]))
    if len(stack) != 1:
        raise ValueError('unbalanced report')
    return root


def _fields(nodes):
    result = {}
    for name, kind, value in nodes:
        if name in result:
            raise ValueError('duplicate field: ' + name)
        result[name] = (kind, value)
    return result


def _shape(fields, required):
    if set(fields) != set(required):
        raise ValueError('unsupported or missing fields')
    for name, kind in required.items():
        if fields[name][0] != kind:
            raise ValueError('wrong field structure: ' + name)


def _bool(value):
    if value not in ('true', 'false'):
        raise ValueError('unsupported boolean')
    return value == 'true'


def parse_display_state(text: str) -> dict:
    """Accept only the measured single-content registry shape, with matched providers."""
    root = _fields(_tree(text))
    _shape(root, {'updateIdentifier': None, 'buildingState': None,
                  'isUpdateInProgress': None, 'providers': '[', 'registries': '['})
    update = root['updateIdentifier'][1]
    if not re.fullmatch(r'[0-9]{1,20}', update):
        raise ValueError('unsupported update identifier')
    building = root['buildingState'][1]
    if not re.fullmatch(r'[A-Za-z]+', building):
        raise ValueError('unsupported building state')
    updating = _bool(root['isUpdateInProgress'][1])
    providers = []
    provider_ids = set()
    for name, kind, nodes in root['providers'][1]:
        match = re.fullmatch(r'Registry\[Registry-(.+) \(line ([0-9]+)\)\]', name)
        if not match or kind != '{' or match[1] in provider_ids:
            raise ValueError('unsupported or duplicate provider')
        provider_ids.add(match[1])
        fields = _fields(nodes)
        _shape(fields, {'status': None})
        providers.append({'id': match[1], 'line': int(match[2]), 'status': fields['status'][1]})
    registries = []
    registry_ids = set()
    for name, kind, nodes in root['registries'][1]:
        match = re.fullmatch(r'Registry-(.+)', name)
        if not match or kind != '{' or match[1] in registry_ids:
            raise ValueError('unsupported or duplicate registry')
        registry_ids.add(match[1])
        fields = _fields(nodes)
        contents = [key for key in fields if key != 'status']
        if len(contents) != 1:
            raise ValueError('expected exactly one preview content')
        title = contents[0]
        _shape(fields, {'status': None, title: '{'})
        content = _fields(fields[title][1])
        _shape(content, {'canvasContent': '{'})
        canvas = _fields(content['canvasContent'][1])
        _shape(canvas, {'isStale': None, 'states': '{'})
        states = _fields(canvas['states'][1])
        _shape(states, {'livePreview': None, 'staticPreview': None,
                        'Light Appearance': None, 'Dark Appearance': None})
        for _, value in states.values():
            if value not in ('disabled', 'succeeded'):
                raise ValueError('unsupported preview state')
        stale = _bool(canvas['isStale'][1])
        live = states['livePreview'][1]
        registries.append({'id': match[1], 'status': fields['status'][1], 'is_stale': stale,
                           'live_preview': live, 'static_preview': states['staticPreview'][1],
                           'reports_fresh_live_success': not stale and live == 'succeeded'})
    if not 1 <= len(registries) <= 32 or registry_ids != provider_ids:
        raise ValueError('unsupported count or provider/registry identity mismatch')
    return {'schema_version': 2, 'authority': 'xcode-ui-diagnostic-report',
            'transport_observed': False, 'report_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'update_identifier': int(update), 'building_state': building,
            'is_update_in_progress': updating, 'providers': providers, 'registries': registries}
