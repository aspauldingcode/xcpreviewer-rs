#!/usr/bin/env python3
"""Collect local Xcode preview evidence without copying Apple binaries."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess


def run(args, destination):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    destination.write_text(result.stdout)
    if result.stderr:
        destination.with_suffix(destination.suffix + '.stderr').write_text(result.stderr)
    return {'command': args, 'exit_code': result.returncode, 'output': destination.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xcode', type=pathlib.Path, default=pathlib.Path('/Applications/Xcode.app'))
    parser.add_argument('--out', type=pathlib.Path, default=pathlib.Path('research/raw'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    contents = args.xcode / 'Contents'
    developer = contents / 'Developer'
    os.environ['DEVELOPER_DIR'] = str(developer)
    if not developer.is_dir():
        parser.error(f'Xcode developer directory missing: {developer}')
    targets = sorted((contents / 'SharedFrameworks').glob('Previews*.framework'))
    paths = [(p.stem, p / p.stem) for p in targets]
    for platform in ['MacOSX', 'iPhoneOS', 'iPhoneSimulator']:
        base = developer / f'Platforms/{platform}.platform/Developer'
        agent = base / 'Library/Xcode/Agents/XCPreviewAgent.app'
        paths.append((platform + '-XCPreviewAgent', agent / ('Contents/MacOS/XCPreviewAgent' if platform == 'MacOSX' else 'XCPreviewAgent')))
        paths.append((platform + '-JITStub', base / 'usr/lib/libPreviewsJITStubExecutor.a'))
    inventory = {'captured_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'xcode': str(args.xcode), 'targets': []}
    inventory['environment'] = []
    for name, command in [('xcode', ['xcodebuild', '-version']), ('os', ['sw_vers']), ('arch', ['uname', '-m'])]:
        inventory['environment'].append(run(command, args.out / f'{name}.txt'))
    for name, path in paths:
        item = {'name': name, 'path': str(path), 'exists': path.is_file()}
        inventory['targets'].append(item)
        if not item['exists']:
            continue
        item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        item['commands'] = []
        for suffix, command in [('file', ['file', str(path)]), ('loads', ['otool', '-L', str(path)]),
                                ('headers', ['otool', '-l', str(path)]), ('symbols', ['nm', '-gU', str(path)]),
                                ('strings', ['/usr/bin/strings', '-a', str(path)])]:
            item['commands'].append(run(command, args.out / f'{name}.{suffix}.txt'))
        symbols = args.out / f'{name}.symbols.txt'
        result = subprocess.run(['xcrun', 'swift-demangle'], input=symbols.read_text(), text=True, capture_output=True)
        (args.out / f'{name}.demangled.txt').write_text(result.stdout)
        item['commands'].append({'command': ['xcrun', 'swift-demangle'], 'exit_code': result.returncode,
                                 'output': f'{name}.demangled.txt'})
        if name == 'PreviewsMessagingHost':
            item['commands'].append(run(['nm', str(path)], args.out / f'{name}.all-symbols.txt'))
            result = subprocess.run(['xcrun', 'swift-demangle'], input=(args.out / f'{name}.all-symbols.txt').read_text(), text=True, capture_output=True)
            (args.out / f'{name}.all-demangled.txt').write_text(result.stdout)
            item['commands'].append({'command': ['xcrun', 'swift-demangle'], 'exit_code': result.returncode,
                                     'output': f'{name}.all-demangled.txt'})
    # SDK stubs describe exports, not implementations. Preserve that distinction.
    sdk = developer / 'Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System/Library/PrivateFrameworks'
    for framework in sorted(sdk.glob('Previews*.framework')):
        stub = framework / f'{framework.stem}.tbd'
        if stub.is_file():
            (args.out / f'{framework.stem}.tbd.txt').write_text(stub.read_text())
            symbols = sorted(set(re.findall(r'_(\$s[^\s,\'\"]+)', stub.read_text())))
            result = subprocess.run(['xcrun', 'swift-demangle'], input='\n'.join(symbols), text=True, capture_output=True)
            (args.out / f'{framework.stem}.sdk-demangled.txt').write_text(result.stdout)
    (args.out / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    failed = [c for t in inventory['targets'] for c in t.get('commands', []) if c['exit_code']]
    print(f"Collected {sum(t['exists'] for t in inventory['targets'])} binaries; {len(failed)} command failures. See {args.out}/inventory.json")
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
