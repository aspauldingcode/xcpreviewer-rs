"""Prepare anchored source-derived modules and independent full native allocations."""
import hashlib
import json
from pathlib import Path
from reloop.primarysource import expected, expression

CLI_RUN = '20261010T222740Z-primary-source-frame-native-extents-89cb7e2c'
CLI_ANCHOR = 'c7d706c527ec6af1fd22709effc05e5a665edfdb28acc33973586cd764e7c834'
NATIVE_RUN = '20261010T215252Z-native-primary-extent-holdouts-5143e5b4'
NATIVE_ANCHOR = '5786fc404ec0181161d42e431b303425260af6adb3d517bf92351cbf542301fa'


def prepare(runs, out):
    """Verify externally pinned inventories before copying bounded owned fixture bytes."""
    runs, out = Path(runs), Path(out)
    out.mkdir(parents=True, exist_ok=False)
    def inventory(run_id, anchor):
        root = runs / run_id
        raw = (root / 'manifest.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != anchor:
            raise ValueError('Corpus prerequisite external anchor changed')
        entries = json.loads(raw)['artifacts']
        rows = {r['path']: r for r in entries}
        if len(rows) != len(entries):
            raise ValueError('Duplicate sealed path')
        def read(relative):
            path = root / relative
            if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink():
                raise ValueError('Unsafe corpus path')
            row = rows[relative]
            if row['bytes'] > 1048576:
                raise ValueError('Corpus artifact byte limit')
            b = path.read_bytes()
            if len(b) != row['bytes'] or hashlib.sha256(b).hexdigest() != row['sha256']:
                raise ValueError('Sealed corpus artifact changed: ' + relative)
            return b
        return read
    cli = inventory(CLI_RUN, CLI_ANCHOR)
    native = inventory(NATIVE_RUN, NATIVE_ANCHOR)
    jobs = json.loads(cli('output/jobs.json'))
    receipts = json.loads(cli('output/receipts.json'))
    if len(jobs) != 42 or len(receipts) != 84:
        raise ValueError('Corpus denominator changed')
    records = []
    def save(b, suffix):
        name = hashlib.sha256(b).hexdigest() + suffix
        target = out / name
        if not target.exists():
            target.write_bytes(b)
        return name
    for i, job in enumerate(jobs):
        if job['index'] != i or bool(job.get('independent_only')) != (i >= 40):
            raise ValueError('Corpus job identity changed')
        c, stride = job['config'], job['stride']
        prediction = expected(c, stride)
        if prediction != cli('output/expected-%d.raw' % i):
            raise ValueError('Independent prediction changed')
        for repeat in range(2):
            r = receipts[i * 2 + repeat]
            text = expression(job['case'], c['reverse'], c['width'], c['height'])
            if r['config'] != c or r['stride'] != stride or r['source_sha256'] != hashlib.sha256(text.encode()).hexdigest():
                raise ValueError('Source receipt identity changed')
            folder = 'output/published/versions/' + r['entry_sha256'] + '/'
            module = cli(folder + 'view.wasm')
            if hashlib.sha256(module).hexdigest() != r['module_sha256']:
                raise ValueError('Module receipt changed')
            observed = None if i >= 40 else native('output/native-%d-%d.raw' % (i, repeat))
            if observed is not None and observed != prediction:
                raise ValueError('Full native prediction mismatch')
            records.append({'job': i, 'repeat': repeat, 'config': c, 'stride': stride,
                            'module': save(module, '.wasm'), 'expected': save(prediction, '.raw'),
                            'native': None if observed is None else save(observed, '.raw'),
                            'source_sha256': r['source_sha256']})
    index = {'version': 1, 'pins': {CLI_RUN: CLI_ANCHOR, NATIVE_RUN: NATIVE_ANCHOR},
             'records': records, 'scope': 'Frozen source-derived modules and full public native callback target allocations; no native Canvas protocol'}
    (out / 'corpus.json').write_text(json.dumps(index, indent=2) + '\n')
    return index
