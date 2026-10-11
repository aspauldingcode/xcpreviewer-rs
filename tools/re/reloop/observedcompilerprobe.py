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
    from reloop.ownedcompilerprobe import corpus as compiler
    fresh=compiler(out/'fresh',observer)
    assert digest(helper)==observer['sha256']
    atomic(out/'provenance.json',{'observer':observer,'source_sha256':digest(source),
                                'compiler_sha256':digest('/usr/bin/clang'),'fresh':fresh})
    return {'observed_compiler_controls':len(result['controls']),
            'observed_loss_cleanup_rejected':failures[0]['record']['report']['drained'] is False and failures[0]['lateWritePresent'],
            'observed_loss_pipe_settlement':failures[0]['record']['emergencyClosed'] and failures[0]['elapsedMs']<6500,
            'observed_output_pressure_drained':failures[1]['record']['report']['drained'] and not failures[1]['lateWritePresent'],
            'observed_private_abort_pipe':result['stdinControl']['stdout']=='stdin-closed\n' and result['stdinControl']['report']['target_code']==0,
            'observed_compiler_late_writes_absent':all(r['lateWriteAbsent'] and r['record']['report']['drained'] for r in result['controls']),
            'observed_fresh_compiler_frames':fresh['fresh_compiler_frames'],
            'observed_fresh_compiler_bytes':fresh['fresh_compiler_bytes']}
