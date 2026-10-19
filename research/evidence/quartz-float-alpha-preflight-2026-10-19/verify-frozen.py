"""Verify the sealed unexecuted preflight; never compiles or launches native code."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import compare as c

p = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--historical-root', type=Path, default=p.parent / 'quartz-alpha-transfer-2026-10-19')
a = parser.parse_args()
seal = c.parsed((p / 'seal.json').read_text())
files = {str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name != 'seal.json' and '__pycache__' not in q.parts}
c.require(files == set(seal['files']), 'complete sealed inventory')
for name, sha in seal['files'].items():
    path = p / name
    c.require(not path.is_symlink() and path.resolve().is_relative_to(p), 'sealed path')
    c.require(c.digest(path.read_bytes()) == sha, 'sealed digest')
for name, sha in c.parsed((p / 'source-pins.json').read_text()).items():
    c.require(c.digest((p / name).read_bytes()) == sha, 'source pin')
old = c.anchored_old(a.historical_root)
relation = c.byte_relation(old[0], old[1])
c.require(relation['mismatch_bytes'] == 9540 and relation['first_mismatch'] == 48, 'historical discriminating contrast')
for name in ['test_compare.py', 'rejected-json-parser.py']:
    for opt, label in [([], 'normal'), (['-O'], 'optimized')]:
        result = subprocess.run([sys.executable, *opt, '-B', str(p / name)], capture_output=True, text=True, timeout=15)
        saved = c.parsed((p / (name + '.' + label + '.json')).read_text())
        c.require(result.returncode == saved['exit'] == 0, 'verification exit')
        if name.startswith('test_'):
            c.require('Ran 6 tests' in result.stderr and 'OK' in result.stderr and 'OK' in saved['stderr'], 'synthetic controls')
        else:
            c.require(c.parsed(result.stdout) == c.parsed(saved['stdout']), 'retained parser failure')
print(json.dumps({'preflight_verified': True, 'synthetic_methods_per_mode': 6,
                  'native_compiled': False, 'native_executed': False,
                  'native_acquisition_qualified': False, 'canvas_qualified': False,
                  'proposed_complete_byte_extent': 172416,
                  'historical_relation_mismatch_bytes': 9540}))
