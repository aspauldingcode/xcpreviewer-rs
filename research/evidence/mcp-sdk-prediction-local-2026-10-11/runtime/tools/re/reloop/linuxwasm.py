"""Bounded Docker execution in an existing Linux VM; no pulls or VM changes."""
import os
import pathlib
import subprocess
import uuid
from reloop.core import Controller, PROJECT_ROOT, ROOT, atomic, digest, load
from reloop.verification import bytes_equal

RUN = '20261009T235049Z-portable-source-second-interpreter-668376cf'
ANCHOR = 'db1ab482584b1fbf0d6e004cdc0197b35500d874663bbe153145446d4bde16f9'
IMAGE = 'sha256:4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109'
WHEEL = '263b924576d9519c43d5a1acff50a03ab03209d16d26c53543c9ab9a409fb93f'


def cleanup_owned(name, owner, out):
    # Name belongs only to this adapter invocation; never stop the VM or user containers.
    ownership = subprocess.run(['docker', 'inspect', '--format', '{{index .Config.Labels "xcpreviewer.owner"}}', name], capture_output=True, text=True, timeout=8)
    cleanup_exit = None
    if ownership.returncode == 0:
        if ownership.stdout.strip() != owner:raise ValueError('Refusing cleanup of unowned container')
        cleanup_exit = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, text=True, timeout=8).returncode
    remaining = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}'], capture_output=True, text=True, timeout=8)
    atomic(out / 'container-cleanup.json', {'owned_name': name, 'ownership_label': owner, 'cleanup_exit': cleanup_exit, 'remaining': remaining.stdout.strip()})
    if remaining.returncode or remaining.stdout.strip():raise ValueError('Owned Linux container cleanup unverified')


def verify_runtime(staging):
    if digest(staging / 'wasmtime-49.0.0.whl') != WHEEL:raise ValueError('Pinned Linux wheel hash mismatch')
    # Verify extracted files against the wheel, so wheel identity alone cannot hide changes.
    import zipfile
    with zipfile.ZipFile(staging / 'wasmtime-49.0.0.whl') as archive:
        expected_files = {entry.filename for entry in archive.infolist() if not entry.is_dir()}
        actual_files = {str(p.relative_to(staging / 'package')) for p in (staging / 'package').rglob('*') if p.is_file()}
        if actual_files != expected_files or any(p.is_symlink() for p in (staging / 'package').rglob('*')):
            raise ValueError('Linux runtime file inventory changed')
        for entry in archive.infolist():
            if entry.is_dir():continue
            if (staging / 'package' / entry.filename).read_bytes() != archive.read(entry):
                raise ValueError('Extracted Linux runtime changed')

def corpus(out):
    out = pathlib.Path(out)
    anchor = Controller(root=PROJECT_ROOT).verify(RUN, ANCHOR)
    if not anchor['valid']:raise ValueError('Source/interpreter evidence anchor mismatch')
    atomic(out / 'source-anchor.json', anchor)
    staging = PROJECT_ROOT / 'research/build/linux-wasmtime'
    verify_runtime(staging)
    owner = uuid.uuid4().hex
    name = 'xcpreviewer-linux-' + owner[:12]
    evidence = PROJECT_ROOT / 'research/runs' / RUN / 'output'
    command = ['docker', 'run', '--rm', '--pull', 'never', '--name', name, '--label', 'xcpreviewer.owner=' + owner, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '256m', '--cpus', '1',
               '--user', '%d:%d' % (os.getuid(), os.getgid()), '--env', 'PYTHONPATH=/runtime', '--env', 'PYTHONDONTWRITEBYTECODE=1',
               '--mount', 'type=bind,src=%s,dst=/evidence,readonly' % evidence,
               '--mount', 'type=bind,src=%s,dst=/runtime,readonly' % (staging / 'package'),
               '--mount', 'type=bind,src=%s,dst=/runner.py,readonly' % (ROOT / 'tools/re/reloop/linux_wasm_runner.py'),
               '--mount', 'type=bind,src=%s,dst=/out' % out,
               '--entrypoint', '/app/.venv/bin/python3', IMAGE, '-B', '/runner.py']
    try:
        with (out / 'linux.stdout').open('wb') as stdout, (out / 'linux.stderr').open('wb') as stderr:
            subprocess.run(command, stdout=stdout, stderr=stderr, check=True, timeout=45)
    finally:
        cleanup_owned(name, owner, out)
    result = load(out / 'linux-execution.json')
    if result['host_system'] != 'Linux' or result['architecture'] != 'aarch64' or result['wasmtime'] != '49.0.0' or len(result['frames']) != 4 or len(result['checker_rows']) != 40:
        raise ValueError('Linux host or control inventory mismatch')
    comparisons = [bytes_equal(evidence / ('pixels-%d.rgba' % i), out / ('linux-%d.rgba' % i)) for i in range(4)]
    if not all(row['passed'] for row in comparisons):raise ValueError('Linux/macOS source output mismatch')
    if result['checker_rows'] != load(evidence / 'source-wasmkit.json')['rows']:raise ValueError('Linux/interpreter checker disagreement')
    atomic(out / 'host-comparisons.json', comparisons)
    atomic(out / 'runtime-identity.json', {'image': IMAGE, 'wheel_sha256': WHEEL, 'wheel_identity': load(staging / 'identity.json')})
    return {'linux_source_verified': True, 'host_system': result['host_system'], 'architecture': result['architecture'],
            'runtime': 'Wasmtime 49.0.0', 'standalone_modules': 4, 'diagnostic_controls': 40,
            'standalone_allocation_bytes_compared': 819200, 'cross_host_pixel_bytes_compared': sum(r['reference_bytes'] for r in comparisons),
            'invalid_requests': result['negative_requests'], 'invalid_allocation_bytes_compared': 3276800, 'imports': result['imports'],
            'owned_container_cleanup_verified': True,
            'scope': 'Exact anchored standalone/diagnostic owned WASM modules on Linux ARM64 Wasmtime in an existing Colima VM on Apple hardware. Direct memory byte comparisons, cross-host pixels and fault controls. macOS source compilation retained; no Linux compiler frontend execution, browser, general SwiftUI, Canvas transport or performance claim.'}
