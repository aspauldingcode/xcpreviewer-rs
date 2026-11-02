"""Pinned owned public observer and optional compiler integration controls."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from reloop.core import ROOT, PROJECT_ROOT, atomic, digest


def corpus(out):
    out=Path(out);out.mkdir()
    frozen=PROJECT_ROOT/'research/evidence/owned-escape-2026-10-10'
    assert digest(frozen/'manifest.json')=='92c1c3a3f8156131a93fb18272377f9369a26fce3080b1c89be006934d509ac0'
    manifest=json.loads((frozen/'manifest.json').read_text())
    for name,row in manifest['files'].items():
        p=frozen/name
        assert '..' not in Path(name).parts and not p.is_symlink()
        assert p.stat().st_size==row['bytes'] and digest(p)==row['sha256']
    source=frozen/'frozen/tools/re/native/OwnedProcessSnapshot.c'
    helper=out/'owned-process-snapshot'
    with (out/'compile.stdout').open('wb') as stdout,(out/'compile.stderr').open('wb') as stderr:
        subprocess.run(['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',str(source),'-lproc','-o',str(helper)],check=True,timeout=10,stdout=stdout,stderr=stderr)
    observer={'helper':str(helper.resolve()),'sha256':digest(helper)}
    with (out/'controls.stdout').open('wb') as stdout,(out/'controls.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observed_compiler_control.js'),
                        str(out/'controls'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable,observer['helper'],observer['sha256']],check=True,timeout=20,stdout=stdout,stderr=stderr)
    result=json.loads((out/'controls/result.json').read_text())
    with (out/'failure-controls.stdout').open('wb') as stdout,(out/'failure-controls.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observed_failure_control.js'),
                        str(out/'failure-controls'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable,observer['helper'],observer['sha256']],check=True,timeout=20,stdout=stdout,stderr=stderr)
    failures=json.loads((out/'failure-controls/result.json').read_text())['controls']
    with (out/'schema-controls.stdout').open('wb') as stdout,(out/'schema-controls.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observer_schema_control.js'),
                        str(out/'schema-controls'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable],check=True,timeout=10,stdout=stdout,stderr=stderr)
    malformed=json.loads((out/'schema-controls/result.json').read_text())['controls']
    with (out/'terminal-controls.stdout').open('wb') as stdout,(out/'terminal-controls.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observer_terminal_control.js'),
                        str(out/'terminal-controls'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable],check=True,timeout=8,stdout=stdout,stderr=stderr)
    terminal=json.loads((out/'terminal-controls/result.json').read_text())['controls']
    with (out/'cancel-boundary.stdout').open('wb') as stdout,(out/'cancel-boundary.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observer_cancel_boundary.js'),
                        str(out/'cancel-boundary'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable,observer['helper'],observer['sha256']],check=True,timeout=8,stdout=stdout,stderr=stderr)
    boundary=json.loads((out/'cancel-boundary/result.json').read_text())
    with (out/'framing-controls.stdout').open('wb') as stdout,(out/'framing-controls.stderr').open('wb') as stderr:
        subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/observer_framing_control.js'),
                        str(out/'framing-controls'),str(ROOT/'tools/re/reloop/observed_compiler.js'),
                        sys.executable],check=True,timeout=8,stdout=stdout,stderr=stderr)
    framing=json.loads((out/'framing-controls/result.json').read_text())['controls']
    from reloop.ownedcompilerprobe import corpus as compiler
    fresh=compiler(out/'fresh',observer)
    assert digest(helper)==observer['sha256']
    atomic(out/'provenance.json',{'observer':observer,'source_sha256':digest(source),
                                'compiler_sha256':digest('/usr/bin/clang'),'fresh':fresh})
    return {'observed_utf8_split_exact':framing[0]['error'] is None and framing[0]['record']['report']['scope']=='owned-é',
            'observed_invalid_utf8_rejected':bool(framing[1]['error']) and framing[1]['record']['report'] is None,
            'observed_ascii_bytewise_exact':framing[2]['error'] is None and framing[2]['record']['report']['scope']=='owned-ascii',
            'observed_terminal_rejections':sum(bool(r['error']) for r in terminal),
            'observed_terminal_valid_control':terminal[0]['error'] is None,
            'observed_reparent_abort_drained':boundary['record']['report']['drained'] and boundary['record']['report']['target_code']==0 and boundary['record']['privateAbortRequested'] and boundary['lateWriteAbsent'],
            'observed_malformed_rows_rejected':len(malformed)==4 and all(r['error'] and r['record']['report']['drained'] is False for r in malformed),
            'observed_compiler_controls':len(result['controls']),
            'observed_loss_cleanup_rejected':failures[0]['record']['report']['drained'] is False and failures[0]['lateWritePresent'],
            'observed_loss_pipe_settlement':failures[0]['record']['emergencyClosed'] and failures[0]['elapsedMs']<6500,
            'observed_output_pressure_drained':failures[1]['record']['report']['drained'] and not failures[1]['lateWritePresent'],
            'observed_private_abort_pipe':result['stdinControl']['stdout']=='stdin-closed\n' and result['stdinControl']['report']['target_code']==0,
            'observed_compiler_late_writes_absent':all(r['lateWriteAbsent'] and r['record']['report']['drained'] for r in result['controls']),
            'observed_fresh_compiler_frames':fresh['fresh_compiler_frames'],
            'observed_fresh_compiler_bytes':fresh['fresh_compiler_bytes']}
