#!/usr/bin/env python3
"""Build a small publishable evidence index from local collection results."""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[2]
raw = root / 'research/raw'
runtime = root / 'research/runtime'
inventory = json.loads((raw / 'inventory.json').read_text())
result = {'scope': 'Initial investigation; synthetic serialization probes, no captured live preview session',
          'captured_at_utc': inventory['captured_at_utc'],
          'environment': {'xcode': (raw / 'xcode.txt').read_text().strip(),
                          'macos': (raw / 'os.txt').read_text().strip(),
                          'architecture': (raw / 'arch.txt').read_text().strip()},
          'binaries': []}
for target in inventory['targets']:
    item = {k: target[k] for k in ['name', 'path', 'exists']}
    if target['exists']:
        item['sha256'] = target['sha256']
        headers = (raw / f"{target['name']}.headers.txt").read_text()
        item['uuids'] = re.findall(r'^\s*uuid ([A-Fa-f0-9-]+)', headers, re.M)
    result['binaries'].append(item)
result['runtime'] = {}
for name in ['os', 'host']:
    data = json.loads((runtime / f'{name}.json').read_text())
    result['runtime'][name] = {'loads': data['loads'], 'images': data['images'],
                              'class_count': len(data['classes']), 'matching_protocol_count': len(data['protocols']),
                              'classes': [c for c in data['classes'] if c['name'] in ['UVPropertyList','UVRawXPCCoder','UVRawXPCDecoder']]}
result['message_keys'] = json.loads((runtime / 'message-keys.json').read_text())
result['synthetic_plist_probe'] = json.loads((runtime / 'plist-probe.json').read_text())
result['static_key_recovery'] = {
    'method': 'Manual ARM64 instruction/string analysis; not live captured payloads',
    'BitmapDescription': {'address': '0x4a8e4', 'keys': ['data', 'width', 'height', 'bytesPerRow', 'byteOrder', 'bitmapInfo', 'bitsPerComponent', 'bitsPerPixel', 'colorSpace']},
    'RenderPayload': {'address': '0x8d6ac', 'keys': ['bitmapDescription', 'selectableRegions', 'snapshotCornerRadius', 'scaleFactor']},
    'LayerHostPayload': {'address': '0x8df88', 'keys': ['contextID', 'scaleFactor', 'width', 'height']},
    'JITLoadCommand': {'address': '0x6fde4', 'keys': ['discriminant', 'command']},
    'JITLoadCommand.LoadDylib': {'address': '0x70528', 'keys': ['path', 'linkage', 'symbolsPath']},
    'BitmapDescription.ByteOrder': {'address': '0x4a1f8', 'raw_values': ['little', 'big']},
    'JITLoadCommand.LoadDylib.Linkage': {'address': '0x70084', 'raw_values': ['strong', 'weak']}}
decompiled = root / 'research/ghidra/messaging-decompiled.txt'
if decompiled.exists():
    output = decompiled.read_text()
    log = (root / 'research/ghidra/headless.log').read_text(errors='replace')
    result['ghidra'] = {'version': '12.1.2', 'language': 'AARCH64:LE:64:AppleSilicon',
                        'selected_function_count': len(re.findall(r'^Address:', output, re.M)),
                        'selected_function_failures': len(re.findall(r'FAILED:|NO FUNCTION', output)),
                        'automatic_analysis_timed_out': 'Analysis timed out at 120 seconds' in log,
                        'project_saved': 'Save succeeded' in log}
# Keep function/property signatures and message cases, not complete symbol tables.
patterns = [r' T .*BitmapDescription\.(?:init\(data:|(?:data|width|height|bytesPerRow|bitmapInfo|bitsPerComponent|bitsPerPixel|colorSpace)\.getter)',
            r' T .*RenderPayload\.(?:init\(bitmapDescription:|(?:bitmapDescription|selectableRegions|snapshotCornerRadius|scaleFactor)\.getter)',
            r' T .*LayerHostPayload\.init\(contextID:', r' S enum case for .*AgentMessageType\.',
            r' T .*LaunchPayload\.init\(workspaceID:', r' T .*JITLoadCommand.LoadDylib\.init\(path:',
            r' T .*HostAgentSystem.AgentEndpoint.Identity\.init\(streamID:',
            r' T .*ForwardPayload\.init\(messageType:', r' T .*MessageTypeKey.getter', r' T .*OneWayMessageKey.getter']
query = re.compile('|'.join(patterns))
result['host_symbols'] = [line for line in (raw / 'PreviewsMessagingHost.demangled.txt').read_text().splitlines() if query.search(line)]
result['sdk_export_signatures'] = {}
for name, query in [('PreviewsServices', r'^PreviewsServices.PreviewsServiceConnection.(?:send\(|Listener.hostToSim\()'),
                    ('PreviewsInjection', r'^(?:PreviewsInjection.__previewsInjection|dispatch thunk of PreviewsInjection.EntryPoint.(?:handleEndpoint|handleHostMessageStream|handleShellMessageStream))')]:
    result['sdk_export_signatures'][name] = [line for line in (raw / f'{name}.sdk-demangled.txt').read_text().splitlines() if re.search(query, line)]
output = root / 'research/evidence/xcode-26.6-macos-26.5.1.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(f'Wrote {output.relative_to(root)}')
