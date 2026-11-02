"""Transactional source-to-frame PNG adapter for the declared primary-layer subset.

The raw frame uses the measured premultiplied callback-target contract. PNG uses
an explicitly defined integer unpremultiplication, not native PNG equivalence.
"""
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import zlib

from reloop.core import atomic, digest, load
from reloop.primarysource import expected, parse, validate
from reloop.sourcecache import build, directory, lock

RUNNER = pathlib.Path(__file__).with_name('source_frame_runner.js')
PAYLOADS = ('source.swift', 'view.c', 'view.ll', 'view.wasm', 'allocation.raw',
            'preview.png', 'runtime.json', 'runtime.stdout', 'runtime.stderr')


def straight_rgba(raw, config, stride):
    validate(config)
    if type(stride) is not int or not config['width'] * 4 <= stride <= 256:
        raise ValueError('Unsupported frame stride')
    if not isinstance(raw, bytes) or len(raw) != 16384:
        raise ValueError('Complete 16384-byte allocation required')
    if raw != expected(config, stride):
        raise ValueError('Frame differs from independent full-allocation prediction')
    pixels = bytearray()
    for y in range(config['height']):
        for x in range(config['width']):
            r, g, b, a = raw[y * stride + x * 4:y * stride + x * 4 + 4]
            if max(r, g, b) > a:
                raise ValueError('Invalid premultiplied pixel')
            pixels.extend((0 if a == 0 else (c * 255 + a // 2) // a for c in (r, g, b)))
            pixels.append(a)
    return bytes(pixels)


def png(rgba, width, height):
    if type(width) is not int or type(height) is not int or not 1 <= width <= 64 or not 1 <= height <= 64:
        raise ValueError('Bounded PNG dimensions required')
    if not isinstance(rgba, bytes) or len(rgba) != width * height * 4:
        raise ValueError('Exact RGBA bytes required')
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'sRGB', b'\0') + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def verify_bundle(folder, anchor):
    if folder.is_symlink() or any(p.is_symlink() for p in folder.iterdir()):
        raise ValueError('Frame bundle symlink rejected')
    if {p.name for p in folder.iterdir()} != set(PAYLOADS) | {'manifest.json'}:
        raise ValueError('Frame bundle inventory changed')
    if digest(folder / 'manifest.json') != anchor:
        raise ValueError('Frame manifest changed')
    manifest = load(folder / 'manifest.json')
    if manifest.get('version') != 1 or set(manifest.get('files', {})) != set(PAYLOADS):
        raise ValueError('Frame manifest schema changed')
    for name in PAYLOADS:
        row = manifest['files'][name]
        if row != {'sha256': digest(folder / name), 'bytes': (folder / name).stat().st_size}:
            raise ValueError('Frame payload changed: ' + name)
    return manifest


def render(source, cache, output, clang, wasm_ld, node, *, stride=None, timeout=5,
           fault_before_commit=False):
    config = parse(source)
    stride = config['width'] * 4 if stride is None else stride
    if type(stride) is not int or not config['width'] * 4 <= stride <= 256:
        raise ValueError('Unsupported frame stride')
    if type(timeout) not in (int, float) or not 0 < timeout <= 10:
        raise ValueError('Runtime deadline must be within ten seconds')
    node = pathlib.Path(node).absolute()
    if not node.is_file():
        raise ValueError('Explicit Node executable required')
    node_hash, runner_hash = digest(node), digest(RUNNER)
    output = directory(output)
    with lock(output, '.frame.lock'):
        versions = directory(output / 'versions')
        stage = pathlib.Path(tempfile.mkdtemp(prefix='.owned-frame-', dir=output))
        try:
            compiled = build(source, cache, stage / 'build', clang, wasm_ld)
            bundle = stage / 'build/versions' / compiled['entry_sha256']
            (stage / 'source.swift').write_text(source)
            for name in ('view.c', 'view.ll', 'view.wasm'):
                shutil.copyfile(bundle / name, stage / name)
            with (stage / 'runtime.stdout').open('wb') as stdout, (stage / 'runtime.stderr').open('wb') as stderr:
                result = subprocess.run([str(node), '--max-old-space-size=64', str(RUNNER),
                                         str(stage / 'view.wasm'), str(stage), str(config['width']),
                                         str(config['height']), str(stride)],
                                        stdout=stdout, stderr=stderr, timeout=timeout)
            if result.returncode:
                raise RuntimeError('WASM frame execution failed: ' + (stage / 'runtime.stderr').read_text()[-4096:])
            if digest(node) != node_hash or digest(RUNNER) != runner_hash:
                raise ValueError('Runtime executable or runner changed during execution')
            raw = (stage / 'allocation.raw').read_bytes()
            rgba = straight_rgba(raw, config, stride)
            runtime = load(stage / 'runtime.json')
            if (runtime.get('imports') != 0 or runtime.get('memory_bytes') != 131072
                    or runtime.get('allocation_bytes') != 16384
                    or runtime.get('rendered_bytes') != stride * config['height']
                    or runtime.get('invalid_requests') != 4 or runtime.get('invalid_unchanged') is not True):
                raise ValueError('Runtime checks missing or invalid')
            (stage / 'preview.png').write_bytes(png(rgba, config['width'], config['height']))
            shutil.rmtree(stage / 'build')
            identity = {'config': config, 'stride': stride, 'source_sha256': compiled['source_sha256'],
                        'module_sha256': digest(stage / 'view.wasm'), 'compiler_entry': compiled['entry_sha256'],
                        'runtime_sha256': node_hash, 'runner_sha256': runner_hash,
                        'adapter_sha256': digest(__file__), 'runtime': runtime,
                        'png_conversion': 'sRGB straight RGBA: zero at alpha 0, floor((premult*255+floor(alpha/2))/alpha) otherwise'}
            manifest = {'version': 1, 'identity': identity,
                        'files': {n: {'sha256': digest(stage / n), 'bytes': (stage / n).stat().st_size}
                                  for n in PAYLOADS}}
            atomic(stage / 'manifest.json', manifest)
            anchor = digest(stage / 'manifest.json')
            verify_bundle(stage, anchor)
            final = versions / anchor
            if final.exists():
                verify_bundle(final, anchor)
            else:
                os.replace(stage, final)
            receipt = {'version': 1, 'entry_sha256': anchor, 'source_sha256': compiled['source_sha256'],
                       'module_sha256': compiled['module_sha256'], 'config': config, 'stride': stride,
                       'png': 'versions/' + anchor + '/preview.png',
                       'allocation': 'versions/' + anchor + '/allocation.raw',
                       'allocation_sha256': manifest['files']['allocation.raw']['sha256'],
                       'png_sha256': manifest['files']['preview.png']['sha256']}
            if fault_before_commit:
                raise RuntimeError('Owned frame pre-publication fault')
            if (output / 'current.json').is_symlink():
                raise ValueError('Frame publish pointer symlink rejected')
            atomic(output / 'current.json', receipt)
            return {**receipt, 'cache_hit': compiled['cache_hit'],
                    'scope': 'Declared primary-layer source to verified premultiplied callback-target allocation and explicitly unpremultiplied PNG. No native PNG equivalence, general SwiftUI, browser, hot reload or state migration.'}
        finally:
            if stage.exists():
                shutil.rmtree(stage)
