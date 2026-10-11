"""Independent mechanical receipt gate; no scientific delivery attestation."""
import hashlib
import json
from pathlib import Path
import sys


def verify(folder):
    folder = Path(folder)
    manifest = json.loads((folder/'manifest.json').read_text())
    listed = set(manifest['files'])
    actual = {str(p.relative_to(folder)) for p in folder.rglob('*')
              if p.is_file() and p.name != 'manifest.json'}
    assert listed == actual, 'Evidence inventory mismatch'
    for name, receipt in manifest['files'].items():
        path = folder/name
        assert not path.is_symlink() and '..' not in Path(name).parts
        data = path.read_bytes()
        assert len(data) == receipt['bytes']
        assert hashlib.sha256(data).hexdigest() == receipt['sha256']
    result = json.loads((folder/'control/result.json').read_text())
    controls = result['controls']
    assert [(r['observed'],r['code']) for r in controls] == [(False,0),(False,7),(True,0),(True,7)]
    for row in controls:
        assert row['late_write'] is (not row['observed'])
        assert row['parent_before'] != row['parent_after']
        assert row['group_after'] == row['child']
        assert len(row['identity']) == 3 and row['identity'][2].startswith('/')
        status = row['target_status']
        assert status['record']['code'] == row['code']
        assert status['record']['anchorReported'] is True
        assert status['record']['signal'] == 'SIGKILL'
        assert (status['error'] is None) == (row['code'] == 0)
        if row['observed']:
            assert row['cleanup']['tracked_processes'] >= 3
    assert result['identity_mutants'] == [{'field':i,'no_signal':True} for i in range(3)]
    return {'controls':4,'identity_mutants':3,'mechanical_verification':'passed',
            'scientific_delivery_review':'pending'}


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1]), sort_keys=True))
