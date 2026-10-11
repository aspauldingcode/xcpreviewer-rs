"""Fresh frozen CLI compilation and bounded owned compiler group controls."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest

CLI_RUN = '20261010T215404Z-primary-source-frame-cli-8a8fd3bc'
CLI_ANCHOR = '9dba73bc8a5098d92441a4bd5e34ada36548f2cbb51387ba2844b6d008cdd4ac'


def corpus(out):
    from reloop.liveswapprobe import anchored
    out = Path(out); out.mkdir()
    controller = Controller(PROJECT_ROOT)
    check = controller.verify(CLI_RUN, CLI_ANCHOR)
    if not check['valid'] or not check['external_anchor_matches']:
        raise ValueError('Frozen compiler CLI prerequisite changed')
    run = controller.runs / CLI_RUN
    identity = json.loads(next((run / 'output/cache/entries').glob('*/manifest.json')).read_text())['identity']
    clang, wasm = Path(identity['clang_invocation']), Path(identity['wasm_ld_invocation'])
    if digest(clang) != identity['clang_sha256'] or digest(wasm) != identity['wasm_ld_sha256']:
        raise ValueError('Compiler/linker identity changed')
    fixture = anchored('research/evidence/source-revision-2026-10-10',
                       'c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac')
    config = {'python': sys.executable, 'cli': str(run / 'source/tools/re/preview_cli.py'),
              'clang': str(clang), 'wasmLd': str(wasm), 'node': shutil.which('node'), 'input': str(fixture)}
    atomic(out / 'config.json', config)
    before = {k: digest(config[k]) for k in ['python', 'node', 'clang', 'wasmLd']}
    with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
        subprocess.run([config['node'], str(ROOT / 'tools/re/tests/owned_compiler_control.js'),
                        str(out / 'config.json'), str(out / 'result')],
                       check=True, timeout=30, stdout=stdout, stderr=stderr)
    with (out / 'orphan.stdout').open('wb') as stdout, (out / 'orphan.stderr').open('wb') as stderr:
        subprocess.run([config['node'], str(ROOT / 'tools/re/tests/owned_orphan_control.js'),
                        str(out / 'orphan-controls'), str(ROOT / 'tools/re/reloop/owned_compiler.js'),
                        config['python'], 'verify'], check=True, timeout=15, stdout=stdout, stderr=stderr)
    orphan = json.loads((out / 'orphan-controls/orphan-result.json').read_text())
    if orphan['failures']:
        raise ValueError('Owned orphan control failed')
    if before != {k: digest(config[k]) for k in before}:
        raise ValueError('Compiler executables changed during probe')
    result = json.loads((out / 'result/compiler-result.json').read_text())
    atomic(out / 'provenance.json', {'frozen_cli_run': CLI_RUN, 'manifest_sha256': CLI_ANCHOR,
                                    'executables': before, 'scope': result['scope']})
    return {'owned_orphan_controls': len(orphan['controls']),
            'owned_target_exits_preserved': [r['code'] for r in orphan['controls']] == [0, 7],
            'fresh_compiler_frames': len(result['records']),
            'fresh_compiler_bytes': sum(r['comparedBytes'] for r in result['records']),
            'compiler_tree_controls': len(result['controls']),
            'compiler_late_writes_absent': all(r['childStarted'] and r['lateWriteAbsent'] for r in result['controls']),
            'source_frontend_cache_misses': sum(not r['cacheHit'] for r in result['builds'])}
