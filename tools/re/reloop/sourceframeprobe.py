"""Source-to-image CLI controls against sealed source/native callback fixtures."""
import json
import pathlib
import shutil
import subprocess
import sys
from fractions import Fraction
from PIL import Image
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.portable import TOOLCHAIN
from reloop.primarysource import expression, expected
from reloop.sourceframe import render
from reloop.browsersource import RUN, ANCHOR
from reloop.verification import bytes_equal


def corpus(out):
    verified = Controller(root=PROJECT_ROOT).verify(RUN, ANCHOR)
    if not verified['valid'] or not verified['external_anchor_matches']:
        raise ValueError('Source-frame reference anchor mismatch')
    atomic(out / 'reference-anchor.json', verified)
    reference = PROJECT_ROOT / 'research/runs' / RUN / 'output'
    cache, published = out / 'cache', out / 'preview'
    node = pathlib.Path(shutil.which('node') or '')
    if not node.is_file():
        raise ValueError('Existing Node executable required')
    source = out / 'input.swift'
    calls, frames, native, pngs, receipts = [], [], [], [], []
    def cli(text, *, success=True, runtime=node, stride=80):
        source.write_text(text)
        index = len(calls)
        argv = [sys.executable, ROOT / 'tools/re/preview_cli.py', source, '--cache', cache,
                '--output', published, '--clang', TOOLCHAIN / 'clang', '--wasm-ld', TOOLCHAIN / 'wasm-ld',
                '--node', runtime, '--stride', stride]
        result = subprocess.run([str(a) for a in argv], capture_output=True, timeout=75)
        (out / ('cli-%d.stdout' % index)).write_bytes(result.stdout)
        (out / ('cli-%d.stderr' % index)).write_bytes(result.stderr)
        calls.append({'index': index, 'exit_code': result.returncode, 'expected_success': success})
        atomic(out / 'calls.json', calls)
        data = json.loads(result.stdout)
        if data['ok'] != success or (result.returncode == 0) != success:
            raise ValueError('Preview CLI exit/result mismatch')
        return data
    inputs = [(expression(4), 0, [68, 80]), (expression(4, 1), 1, [68, 80]),
              (expression(12, 0, 1, 1), 14, [4, 16]), (expression(19, 1, 64, 64), 15, [256, 256])]
    for text, ref_index, strides in inputs:
        for stride in strides:
            for repeat in range(2):
                receipt = cli(text, stride=stride); receipts.append(receipt)
                index = len(receipts) - 1
                folder = published / 'versions' / receipt['entry_sha256']
                cfg = receipt['config']; prediction = expected(cfg, stride)
                path = out / ('expected-%d.raw' % index); path.write_bytes(prediction)
                target = out / ('frame-%d.raw' % index); shutil.copyfile(folder / 'allocation.raw', target)
                frames.append(bytes_equal(path, target))
                if stride == 80 and cfg['width'] == 17:
                    native.append(bytes_equal(reference / ('native-%d-1-0.raw' % ref_index), target))
                # Separate Fraction projection, then Pillow decodes the produced PNG.
                pixels = bytearray()
                for y in range(cfg['height']):
                    for x in range(cfg['width']):
                        p = prediction[y * stride + x * 4:y * stride + x * 4 + 4]
                        pixels.extend(0 if not p[3] else int(Fraction(c * 255, p[3]) + Fraction(1, 2)) for c in p[:3])
                        pixels.append(p[3])
                image = Image.open(folder / 'preview.png')
                same = (image.size == (cfg['width'], cfg['height']) and image.mode == 'RGBA'
                        and image.info.get('srgb') == 0 and image.tobytes() == bytes(pixels))
                pngs.append({'index': index, 'bytes': len(pixels), 'passed': same})
                shutil.copyfile(folder / 'preview.png', out / ('preview-%d.png' % index))
                module_check = bytes_equal(reference / ('source-%d.wasm' % ref_index), folder / 'view.wasm')
                if not module_check['passed']:
                    raise ValueError('Preview module differs from anchored source compiler output')
    if not all(r['passed'] for r in frames + native + pngs):
        raise ValueError('Preview raw/native/decoded PNG mismatch')
    pointer = published / 'current.json'; before = pointer.read_bytes(); last = load(pointer)
    last_png = digest(published / last['png']); failures = []
    def preserved(name):
        if pointer.read_bytes() != before or digest(published / last['png']) != last_png:
            raise ValueError('Failed preview replaced last valid image')
        failures.append({'control': name, 'last_good_preserved': True})
    cli('Text("unsupported")', success=False); preserved('unsupported-source')
    cli(inputs[0][0], success=False, stride=67); preserved('invalid-stride')
    cli(inputs[0][0], success=False, runtime=pathlib.Path('/usr/bin/false')); preserved('runtime-exit')
    # Use the published module's matching cache entry for the specific failing text.
    from reloop.sourcecache import build
    built = build(inputs[0][0], cache, out / 'build-control', TOOLCHAIN / 'clang', TOOLCHAIN / 'wasm-ld')
    entry = cache / 'entries' / built['entry_sha256']
    module = entry / 'view.wasm'; old = module.read_bytes(); module.write_bytes(old + b'bad')
    try:
        cli(inputs[0][0], success=False); preserved('corrupt-cached-module')
    finally:
        module.write_bytes(old)
    try:
        render(inputs[0][0], cache, published, TOOLCHAIN / 'clang', TOOLCHAIN / 'wasm-ld', node,
               fault_before_commit=True)
    except RuntimeError as error:
        if str(error) != 'Owned frame pre-publication fault':
            raise
        preserved('pre-publication-fault')
    else:
        raise ValueError('Missing frame publication fault')
    # A deterministic owned runtime timeout fixture, not a browser fallback.
    sleeper = out / 'owned-timeout'; sleeper.write_text('#!/bin/sh\nexec /bin/sleep 2\n'); sleeper.chmod(0o700)
    try:
        render(inputs[0][0], cache, published, TOOLCHAIN / 'clang', TOOLCHAIN / 'wasm-ld', sleeper, timeout=0.1)
    except subprocess.TimeoutExpired:
        preserved('runtime-timeout')
    else:
        raise ValueError('Missing owned runtime timeout')
    if list(published.glob('.owned-frame-*')):
        raise ValueError('Frame staging cleanup incomplete')
    atomic(out / 'receipts.json', receipts)
    atomic(out / 'comparisons.json', {'frames': frames, 'native': native, 'pngs': pngs})
    atomic(out / 'failure-controls.json', failures)
    return {'frames': len(frames), 'allocation_bytes': len(frames) * 16384,
            'native_frames': len(native), 'native_target_bytes': len(native) * 720,
            'pngs': len(pngs), 'png_decoded_bytes': sum(r['bytes'] for r in pngs),
            'all_frames_equal': True, 'all_native_equal': True, 'all_pngs_equal': True,
            'invalid_requests': len(frames) * 4, 'failure_controls': len(failures),
            'all_failed_previews_preserve_last_good': True, 'staging_cleanup': True,
            'scope': 'Primary-layer source CLI to fixed-memory import-free V8 frame and independently decoded sRGB PNG, explicit integer unpremultiplication. Native callback prefixes only; no native PNG equivalence, browser/Canvas wire, general SwiftUI, state migration or hot reload.'}
