"""Separately compiled full-buffer checker for source-derived IR, no LTO."""
import hashlib
from reloop.core import ROOT, atomic, digest, load
from reloop.portable import TOOLCHAIN
from reloop.wasmkit import parse_result


def checker(length, stride, width):
    if any(type(v) is not int for v in (length, stride, width)) or not 1 <= width <= 320 or not width * 4 <= stride <= 1280 or not 1 <= length <= 204800 or length % stride or length // stride > 160:
        raise ValueError('Bounded source checker geometry required')
    return '''#include "expectations.h"
extern unsigned render(unsigned);
extern unsigned char *pixels(void);
extern unsigned capacity(void);
static unsigned compare(void) {
    unsigned count = 0;
    unsigned char *output = pixels();
    for (unsigned i = 0; i < 204800; ++i)
        count += output[i] != (i < %d ? expected[i] : 0xa5);
    return count;
}
static unsigned prepare(void) {
    if (capacity() != 204800) return 0;
    unsigned char *output = pixels();
    for (unsigned i = 0; i < 204800; ++i) output[i] = 0xa5;
    return render(%d) == %d;
}
unsigned verify(unsigned mutation) {
    if (mutation > 3 || !prepare()) return ~0u;
    unsigned char *output = pixels();
    if (mutation == 1) output[0] ^= 1;
    if (mutation == 2) output[%d] ^= 1;
    if (mutation == 3) output[204799] ^= 1;
    return compare();
}
unsigned verify_rejected(unsigned index) {
    const unsigned invalid[4] = {0, %d, 1281, ~0u};
    if (index > 3 || !prepare()) return ~0u;
    if (render(invalid[index]) != 0) return ~0u;
    return compare();
}
''' % (length, stride, length, length - 1, width * 4 - 1)


def expected_count(function, argument):
    if function not in ('verify', 'verify_rejected') or type(argument) is not int or argument < 0:
        raise ValueError('Unknown checker call domain')
    if argument > 3:
        return 0xffffffff
    return int(function == 'verify' and argument != 0)


def verify(out, command, jobs):
    runtime = TOOLCHAIN / 'wasmkit'
    if not runtime.is_file():raise ValueError('Existing WasmKit required; no fallback')
    command([runtime, '--version'], 'source-wasmkit-version')
    modules = []; rows = []
    calls = [('verify', i) for i in range(5)] + [('verify_rejected', i) for i in range(5)]
    for job in jobs:
        index = job['index'];root = out / ('checker-%d' % index);root.mkdir()
        # Native decoded pixels supply full-size expectations; padding is independently literal.
        reference = out / (('native-%d.rgba' if index < 3 else 'expected-%d.rgba') % index)
        raw = reference.read_bytes();stride = job['stride'];width = job['config']['width']
        ir = out / ('source-%d.ll' % index)
        if digest(ir) != job['ir_sha256']:raise ValueError('Saved renderer IR changed before checker link')
        (root / 'expectations.h').write_text('static const unsigned char expected[%d]={%s};\n' % (len(raw), ','.join(map(str, raw))))
        source = root / 'checker.c';source.write_text(checker(len(raw), stride, width));obj = root / 'checker.o';module = root / 'checked.wasm'
        # Separate translation unit + object, no LTO: checker cannot fold the renderer away.
        command([TOOLCHAIN / 'clang', '--target=wasm32', '-O2', '-nostdlib', '-fno-builtin', '-I', root, '-c', source, '-o', obj], 'source-checker-object-%d' % index)
        command([TOOLCHAIN / 'clang', '--target=wasm32', '-O2', '-nostdlib', '-fno-builtin', '-fuse-ld=' + str(TOOLCHAIN / 'wasm-ld'), ir, obj,
                 '-Wl,--no-entry', '-Wl,--strip-all', '-Wl,--export=verify', '-Wl,--export=verify_rejected',
                 '-Wl,--initial-memory=1048576', '-Wl,--max-memory=1048576', '-o', module], 'source-checker-link-%d' % index)
        modules.append({'index': index, 'module': str(module), 'module_sha256': digest(module), 'renderer_ir_sha256': digest(ir),
                        'reference_sha256': hashlib.sha256(raw).hexdigest(), 'reference_bytes': len(raw)})
        for function, argument in calls:
            name = 'source-wasmkit-%d-%s-%d' % (index, function, argument)
            command([runtime, 'run', module, function, 'i32:' + str(argument)], name)
            actual = parse_result((out / (name + '.stdout')).read_text());expected = expected_count(function, argument)
            rows.append({'module': index, 'function': function, 'argument': argument, 'actual': actual, 'expected': expected, 'passed': actual == expected})
    atomic(out / 'checker-modules.json', modules)
    command(['node', ROOT / 'tools/re/reloop/sourceinterpreter_runner.js', out / 'checker-modules.json', out / 'source-v8-checker.json'], 'source-v8-checker')
    v8 = load(out / 'source-v8-checker.json')
    atomic(out / 'source-wasmkit.json', {'rows': rows, 'modules': modules, 'runtime_sha256': digest(runtime), 'v8': v8,
           'scope': 'New diagnostic modules link the unchanged saved source renderer IR and separate non-LTO checker. WasmKit CLI returns whole-buffer mismatch counts, not memory dumps. Both hosts run on macOS.'})
    if not all(row['passed'] for row in rows) or v8['rows'] != rows:
        raise ValueError('Source checker interpreter disagreement')
    return {'source_second_runtime': 'WasmKit', 'source_second_runtime_controls': len(rows), 'source_second_runtime_all_passed': True,
            'source_second_baseline_buffer_bytes_compared': len(jobs) * 204800,
            'source_second_invalid_buffer_bytes_compared': len(jobs) * 4 * 204800,
            'source_second_mutation_controls': len(jobs) * 3, 'source_checker_v8_agrees': True, 'source_checker_imports': v8['imports'],
            'scope_second_runtime': 'Unchanged saved source IR linked with separate full-buffer checker into new diagnostic modules, executed by WasmKit and V8 on macOS. Not the original standalone module bytes; no browser/non-Apple host or broader SwiftUI claim.'}
