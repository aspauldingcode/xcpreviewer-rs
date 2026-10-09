"""Strict literal expression subset to C/LLVM/WASM; not a general Swift compiler."""
import json
import pathlib
import re
import subprocess
from PIL import Image
from reloop.core import ROOT, PROJECT_ROOT, Controller, atomic, digest, load
from reloop.portable import TOOLCHAIN, ORACLE_RUN, ORACLE_ANCHOR
from reloop.verification import bytes_equal

GRAMMAR = re.compile(r'\s*Color\s*\(\s*\.sRGB\s*,\s*red\s*:\s*([01])\s*,\s*green\s*:\s*0\s*,\s*blue\s*:\s*([01])\s*,\s*opacity\s*:\s*1\s*\)\s*\.\s*frame\s*\(\s*width\s*:\s*([0-9]{1,3})\s*,\s*height\s*:\s*([0-9]{1,3})\s*\)\s*', re.ASCII)


def parse(source):
    if type(source) is not str or len(source) > 4096 or not source.isascii():
        raise ValueError('Bounded ASCII expression required')
    match = GRAMMAR.fullmatch(source)
    if not match:
        raise ValueError('Unsupported expression outside literal Color.frame contract')
    red, blue, width, height = match.groups()
    if (red, blue) not in [('1', '0'), ('0', '1')]:
        raise ValueError('Only opaque literal sRGB red/blue accepted')
    color = 'red' if red == '1' else 'blue'
    width, height = int(width), int(height)
    if not 1 <= width <= 320 or not 1 <= height <= 160:
        raise ValueError('Frame dimensions outside contract')
    return {'color': color, 'width': width, 'height': height}


def lower(config):
    # Revalidate rather than accepting executable strings from a caller.
    if set(config) != {'color', 'width', 'height'} or config['color'] not in ('red', 'blue') or any(type(config[k]) is not int for k in ('width', 'height')):
        raise ValueError('Invalid literal source configuration')
    if not 1 <= config['width'] <= 320 or not 1 <= config['height'] <= 160:
        raise ValueError('Frame dimensions outside contract')
    w, h = config['width'], config['height']
    r, b = (255, 0) if config['color'] == 'red' else (0, 255)
    return '''static unsigned char buffer[204800];
unsigned char *pixels(void) { return buffer; }
unsigned capacity(void) { return sizeof(buffer); }
unsigned render(unsigned stride) {
    if (stride < %d || stride > 1280) return 0;
    for (unsigned y = 0; y < %d; ++y) {
        for (unsigned x = 0; x < %d; ++x) {
            unsigned i = y * stride + x * 4;
            buffer[i] = %d; buffer[i+1] = 0;
            buffer[i+2] = %d; buffer[i+3] = 255;
        }
        for (unsigned i = %d; i < stride; ++i) buffer[y*stride+i] = 0xcd;
    }
    return stride * %d;
}
''' % (w * 4, h, w, r, b, w * 4, h)


def stable_ir(text):
    """Normalize only compiler file metadata; preserve every remaining IR byte."""
    lines = text.splitlines(keepends=True)
    if len(lines) < 3 or not lines[0].startswith('; ModuleID = ') or not lines[1].startswith('source_filename = '):
        raise ValueError('Unexpected LLVM source metadata header')
    return '; ModuleID = \'literal-view.c\'\nsource_filename = "literal-view.c"\n' + ''.join(lines[2:])


HOLDOUTS = [
    'Text("red")',
    'Color.red.frame(width: 320, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320, height: 160).opacity(0.5)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: width, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: -1, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320.0, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(height: 160, width: 320)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 321, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320, height: 161)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 0, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320, height: 160);system("bad")',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 0.5).frame(width: 320, height: 160)',
    'Color(.sRGB, red: 1, green: 1, blue: 0, opacity: 1).frame(width: 320, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 1, opacity: 1).frame(width: 320, height: 160)',
    'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: ３２０, height: 160)',
]


def corpus(out):
    out = pathlib.Path(out)
    anchor = Controller(root=PROJECT_ROOT).verify(ORACLE_RUN, ORACLE_ANCHOR)
    if not anchor['valid']:
        raise ValueError('Native renderer oracle anchor mismatch')
    atomic(out / 'native-anchor.json', anchor)
    def command(args, name):
        with (out / (name + '.stdout')).open('wb') as stdout, (out / (name + '.stderr')).open('wb') as stderr:
            subprocess.run([str(a) for a in args], stdout=stdout, stderr=stderr, check=True, timeout=30)
    command([TOOLCHAIN / 'clang', '--version'], 'llvm-version')
    jobs = []
    for index, fixture in enumerate(['red.swift', 'red.swift', 'blue.swift', 'padded.swift']):
        source = ROOT / 'tools/re/fixtures/LiteralViewSubset' / fixture
        text = source.read_text();config = parse(text)
        (out / ('source-%d.swift' % index)).write_text(text)
        c = out / ('source-%d.c' % index);ir = out / ('source-%d.ll' % index);module = out / ('source-%d.wasm' % index)
        c.write_text(lower(config))
        command([TOOLCHAIN / 'clang', '--target=wasm32', '-O2', '-nostdlib', '-fno-builtin', '-emit-llvm', '-S', c, '-o', ir], 'ir-%d' % index)
        raw_ir = ir.read_text()
        (out / ('source-%d.raw.ll' % index)).write_text(raw_ir)
        ir.write_text(stable_ir(raw_ir))
        if 'target triple = "wasm32' not in ir.read_text() or 'define' not in ir.read_text():
            raise ValueError('Generated LLVM IR lacks wasm32 definitions')
        # Link the saved IR, not the C file: source -> C -> LLVM -> WASM is exercised.
        command([TOOLCHAIN / 'clang', '--target=wasm32', '-O2', '-nostdlib', '-fno-builtin', '-fuse-ld=' + str(TOOLCHAIN / 'wasm-ld'), ir,
                 '-Wl,--no-entry', '-Wl,--strip-all', '-Wl,--export=render', '-Wl,--export=pixels', '-Wl,--export=capacity',
                 '-Wl,--initial-memory=327680', '-Wl,--max-memory=327680', '-o', module], 'link-%d' % index)
        jobs.append({'index': index, 'module': str(module), 'stride': config['width'] * 4 + (4 if index == 3 else 0),
                     'config': config, 'source_sha256': digest(source), 'ir_sha256': digest(ir), 'module_sha256': digest(module)})
    atomic(out / 'jobs.json', jobs)
    command(['node', ROOT / 'tools/re/reloop/viewsource_runner.js', out / 'jobs.json', out], 'execute')
    execution = load(out / 'execution.json');comparisons = [];native_comparisons = []
    for job in jobs:
        i = job['index'];cfg = job['config'];stride = job['stride']
        # Literal byte expectations are independent of the source lowering/code generator.
        pixel = {'red': b'\xff\x00\x00\xff', 'blue': b'\x00\x00\xff\xff'}[cfg['color']]
        raw = (pixel * cfg['width'] + b'\xcd' * (stride - cfg['width'] * 4)) * cfg['height']
        expected = out / ('expected-%d.rgba' % i);expected.write_bytes(raw)
        comparisons.append(bytes_equal(expected, out / ('pixels-%d.rgba' % i)))
        if i < 3:
            with Image.open(PROJECT_ROOT / 'research/runs' / ORACLE_RUN / 'output' / ('solid-%d.png' % i)) as image:
                if image.size != (cfg['width'], cfg['height']):raise ValueError('Native oracle geometry mismatch')
                native = out / ('native-%d.rgba' % i);native.write_bytes(image.convert('RGBA').tobytes())
            native_comparisons.append(bytes_equal(native, out / ('pixels-%d.rgba' % i)))
    rejected = []
    for source in HOLDOUTS:
        try:parse(source)
        except ValueError:rejected.append(source)
        else:raise ValueError('Unsupported source holdout accepted')
    atomic(out / 'comparisons.json', {'literal': comparisons, 'native': native_comparisons})
    atomic(out / 'holdouts.json', {'rejected': rejected})
    atomic(out / 'tool-identities.json', {'clang_sha256': digest(TOOLCHAIN / 'clang'), 'wasm_ld_sha256': digest(TOOLCHAIN / 'wasm-ld'), 'node': execution['node'], 'v8': execution['v8']})
    repeat = bytes_equal(out / 'pixels-0.rgba', out / 'pixels-1.rgba')['passed']
    return {'source_modules': len(jobs), 'all_native_rgba_equal': all(r['passed'] for r in native_comparisons),
            'native_compared_bytes': sum(r['reference_bytes'] for r in native_comparisons),
            'all_literal_padding_equal': all(r['passed'] for r in comparisons), 'literal_compared_bytes': sum(r['reference_bytes'] for r in comparisons),
            'source_holdouts_rejected': len(rejected), 'repeat_pixels_equal': repeat, 'repeat_module_bytes_equal': jobs[0]['module_sha256'] == jobs[1]['module_sha256'], 'repeat_ir_bytes_equal': jobs[0]['ir_sha256'] == jobs[1]['ir_sha256'],
            'wasm_imports': execution['imports'], 'negative_requests': execution['negative_requests'], 'invalid_buffer_unchanged': execution['invalid_buffer_unchanged'],
            'scope': 'Strict ASCII explicit opaque sRGB red/blue Color.frame expression subset, bounded integer geometry. Custom lowering through saved C/LLVM IR to import-free WASM in Node V8 on macOS. Frozen native ImageRenderer reference; no Swift compiler, general SwiftUI, browser/non-Apple execution, live Canvas transport or hot-reload/performance claim.'}
