"""One bounded frozen adapter for corpus, failed proposals, close and source gates."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from reloop.core import ROOT, PROJECT_ROOT
from reloop.livecorpus import prepare


def anchored(relative, anchor):
    folder = PROJECT_ROOT / relative
    raw = (folder / 'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != anchor:
        raise ValueError('Adapter fixture external anchor changed')
    for row in json.loads(raw)['files']:
        data = (folder / row['path']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Adapter fixture payload changed')
    return folder


def corpus(out):
    out = Path(out)
    node = shutil.which('node')
    if not node:
        raise ValueError('Existing Node required')
    def run(script, args, seconds):
        name = Path(script).stem
        with (out / (name + '.stdout')).open('wb') as stdout, (out / (name + '.stderr')).open('wb') as stderr:
            subprocess.run([node, str(ROOT / 'tools/re' / script), *map(str, args)],
                           check=True, timeout=seconds, stdout=stdout, stderr=stderr)
    prepare(PROJECT_ROOT / 'research/runs', out / 'corpus-inputs')
    run('reloop/live_wasm_corpus.js', [out / 'corpus-inputs', out / 'frames'], 45)
    baseline = anchored('research/evidence/live-wasm-swap-2026-10-10',
                        '7a77937fb1d32207ed6eac1ee7dac88a959150222f5485ad5ac69af8d622ff64')
    controls = out / 'failure-controls'; controls.mkdir()
    for name in ('fixtures.json', '0-view.wasm', '1-view.wasm', '0-allocation.raw', '1-allocation.raw'):
        shutil.copyfile(baseline / name, controls / name)
    run('tests/live_wasm_host_control.js', [controls], 15)
    run('tests/live_wasm_cancel_control.js', [controls, 'after', baseline], 15)
    run('tests/live_wasm_guard_control.js', [controls, ROOT / 'tools/re/reloop/live_wasm_host.js', 'verify', baseline], 20)
    source = anchored('research/evidence/source-revision-2026-10-10', SOURCE_ANCHOR)
    source_inputs = out / 'source-inputs'; source_inputs.mkdir()
    for name in ['fixtures.json'] + ['%d-%s' % (i, suffix) for i in range(3)
                                   for suffix in ('source.swift', 'view.wasm', 'expected.raw')]:
        shutil.copyfile(source / name, source_inputs / name)
    run('tests/source_revision_control.js', [source_inputs, controls], 15)
    run('tests/source_file_loop_control.js', [source_inputs, out / 'file-controls'], 15)
    run('tests/source_input_control.js', [out / 'input-controls', ROOT / 'tools/re/reloop/source_file_loop.js'], 5)
    inputs = json.loads((out / 'input-controls/result.json').read_text())['controls']
    file_loop = json.loads((out / 'file-controls/file-loop-result.json').read_text())
    frames = json.loads((out / 'frames/result.json').read_text())
    faults = json.loads((controls / 'control-result.json').read_text())
    cancel = json.loads((controls / 'after-fix.json').read_text())
    guards = json.loads((controls / 'guard-result.json').read_text())
    if guards['failures'] or len(guards['controls']) != 5:
        raise ValueError('Adapter reentrant guard gate failed')
    revisions = json.loads((controls / 'source-result.json').read_text())
    if not cancel['settled_at_close'] or cancel['status_at_close']['liveWorkers'] != 0:
        raise ValueError('Adapter cancellation gate failed')
    facts = {'frames': len(frames['records']),
             'file_input_controls': len(inputs),
             'file_input_descriptors_closed': all(r['opened'] == r['closed'] for r in inputs),
             'file_fifo_deadline_closed': inputs[0]['deadlineAutoClosed'],
             'file_revisions': file_loop['accepted'],
             'file_serialized_read': file_loop['serializedLiveRead'],
             'file_controls': len(file_loop['controls']),
             'file_builder_aborts': file_loop['aborts'],
             'file_deadline_aborts': file_loop['deadlineAborts'],
             'file_loop_quiescent': file_loop['final_status']['timers'] == 0 and not file_loop['final_status']['building'],
             'native_bytes': sum(r['native_bytes'] for r in frames['records']),
             'independent_bytes': sum(r['independent_bytes'] for r in frames['records']),
             'failed_proposals': len(faults['faults']),
             'close_controls': 1 + len(cancel['extra_controls']),
             'closed_guard_controls': sum(r['case'].startswith('close-in-guard-') for r in guards['controls']),
             'guard_rejections': sum(r['case'].startswith('guard-') for r in guards['controls']),
             'source_rejections': len(revisions['controls']),
             'source_revisions': revisions['accepted_revisions'],
             'zero_workers': frames['final_status']['liveWorkers'] == 0 and revisions['final_status']['liveWorkers'] == 0,
             'scope': 'Frozen owned runtime policy controls, reused public native corpus; no Canvas sequencing or scientific delivery acceptance'}
    from reloop.ownedcompilerprobe import corpus as fresh_compiler
    facts.update(fresh_compiler(out / 'fresh-compiler'))
    from reloop.observedcompilerprobe import corpus as observed_compiler
    facts.update(observed_compiler(out / 'observed-compiler'))
    from reloop.rustframeprobe import corpus as rust_frame
    facts.update(rust_frame(out / 'rust-frame'))
    (out / 'result.json').write_text(json.dumps({'observations': facts}, indent=2) + '\n')
    return facts


SOURCE_ANCHOR = 'c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac'
