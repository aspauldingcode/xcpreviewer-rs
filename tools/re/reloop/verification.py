"""Exact comparison and typed value fingerprints. No implicit normalization."""
import datetime
import hashlib
import pathlib
import struct


def bytes_equal(reference, candidate):
    """Stream every byte, including unmatched tails; retain bounded diagnostics."""
    paths = [pathlib.Path(reference), pathlib.Path(candidate)]
    hashes = [hashlib.sha256(), hashlib.sha256()]
    lengths = [0, 0]
    different = bits = offset = 0
    first = []
    with paths[0].open('rb') as left, paths[1].open('rb') as right:
        while True:
            a, b = left.read(65536), right.read(65536)
            if not a and not b:
                break
            for i, chunk in enumerate([a, b]):
                hashes[i].update(chunk)
                lengths[i] += len(chunk)
            # Native bytes equality examines the complete chunk; hashes/lengths above
            # still cover every byte. Expand diagnostics only for unequal chunks.
            if a == b:
                offset += len(a)
                continue
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else None
                y = b[i] if i < len(b) else None
                if x == y:
                    continue
                different += 1
                if x is not None and y is not None:
                    bits += bin(x ^ y).count('1')
                if len(first) < 32:
                    first.append({'offset': offset + i, 'reference': x, 'candidate': y})
            offset += max(len(a), len(b))
    return {'mode': 'exact-bytes', 'passed': different == 0,
            'reference_bytes': lengths[0], 'candidate_bytes': lengths[1],
            'reference_sha256': hashes[0].hexdigest(), 'candidate_sha256': hashes[1].hexdigest(),
            'different_bytes': different, 'different_bits_in_shared_extent': bits,
            'unmatched_tail_bytes': abs(lengths[0] - lengths[1]), 'first_mismatches': first,
            'normalization': 'none',
            'scope': 'Equality of these files only; oracle independence and behavioral coverage must be established separately.'}


def typed(value):
    """Canonical typed plist value. Equality does not collapse bool/int or -0/+0."""
    if type(value) is dict:
        return ('dict', tuple(sorted((key, typed(item)) for key, item in value.items())))
    if type(value) is list:
        return ('array', tuple(typed(item) for item in value))
    if type(value) is float:
        return ('float64', struct.pack('>d', value).hex())
    if type(value) is datetime.datetime:
        return ('date', value.isoformat(timespec='microseconds'))
    if type(value) in {str, int, bool, bytes}:
        return (type(value).__name__, value)
    raise ValueError('Unsupported plist value type: ' + type(value).__name__)


def sealed_compare(controller, reference, candidate):
    from reloop.evidence import artifact
    from reloop.core import digest, load
    for item in (reference, candidate):
        if not isinstance(item, dict) or set(item) != {'run_id', 'path'}:
            raise ValueError('Comparison requires two sealed artifact references')
    paths = [artifact(controller, item['run_id'], item['path']) for item in [reference, candidate]]
    anchors = []; expected = []
    for item in [reference, candidate]:
        manifest = controller.runs/item['run_id']/'manifest.json'
        anchors.append(digest(manifest))
        expected.append(next(a['sha256'] for a in load(manifest)['artifacts'] if a['path']==item['path']))
    result = bytes_equal(*paths)
    for i, item in enumerate([reference, candidate]):
        side = 'reference' if i == 0 else 'candidate'
        if result[side+'_sha256'] != expected[i] or not controller.verify(item['run_id'], anchors[i])['valid']:
            raise RuntimeError('Evidence changed during comparison')
    return {**result, 'reference': reference, 'candidate': candidate, 'manifest_sha256': anchors}
