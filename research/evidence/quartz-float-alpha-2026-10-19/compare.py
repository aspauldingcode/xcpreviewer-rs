"""Raw-byte comparison only. Never establishes native acquisition or Canvas acceptance."""
import hashlib
import json
import math
import struct
from pathlib import Path

OLD_SEAL = 'e6b5d771110e5ce83317865f42a78a4d8021cd6179a898bf7e45f37823079851'
WIDTH, HEIGHT, STRIDE, PROVIDER_SIZE, DEST_SIZE = 768, 3, 12352, 37056, 49152

def require(value, message):
    if not value:
        raise ValueError(message)

def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result

def parsed(raw):
    def bad(value):
        raise ValueError('non-finite JSON constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    def finite(item):
        if type(item) is float:
            require(math.isfinite(item), "non-finite JSON number")
        elif type(item) is dict:
            for child in item.values(): finite(child)
        elif type(item) is list:
            for child in item: finite(child)
    finite(value)
    return value

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]

def expected_provider():
    # Python independently generates each little-endian Float32 field. No C output read.
    result = bytearray(b'\xa5' * PROVIDER_SIZE)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            alpha = f32(f32(x // 3) * f32(1 / 255))
            rgb = [0.0, 0.0, 0.0]
            rgb[x % 3] = alpha
            offset = y * STRIDE + x * 16
            result[offset:offset + 16] = struct.pack('<4f', *rgb, alpha)
    return bytes(result)

def expected_identity():
    return expected_provider() + b'\xa5' * (DEST_SIZE - PROVIDER_SIZE)

def byte_relation(actual, expected):
    require(len(actual) == len(expected), 'relation length')
    differences = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
    return {'bytes_compared': len(actual), 'mismatch_bytes': len(differences),
            'first_mismatch': differences[0] if differences else None,
            'exact': not differences}

def anchored_old(root):
    root = Path(root)
    raw = (root / 'seal.json').read_bytes()
    require(digest(raw) == OLD_SEAL, 'historical seal identity')
    seal = parsed(raw)
    for name, sha in seal['files'].items():
        path = root / name
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), 'historical path')
        require(digest(path.read_bytes()) == sha, 'historical member')
    result = []
    for route in range(2):
        name = 'route%d-readback.raw' % route
        # Locate the member by its exact basename; reject ambiguity or absence.
        members = [n for n in seal['files'] if Path(n).name == name]
        require(len(members) == 1, 'historical route identity')
        value = (root / members[0]).read_bytes()
        require(len(value) == DEST_SIZE, 'historical layout')
        result.append(value)
    require(result[1] == expected_identity(), 'historical linear identity')
    require(result[0] != result[1], 'historical discriminating contrast')
    return result

def compare(root, rows, old):
    root = Path(root)
    require(type(rows) is list and len(rows) == 2, 'route count')
    require(type(old) is list and len(old) == 2 and all(type(x) is bytes and len(x) == DEST_SIZE for x in old), 'historical arrays')
    provider = expected_provider()
    identity = expected_identity()
    require(old[1] == identity and old[0] != identity, 'historical discriminating inputs')
    outputs = []
    pids = []
    for route, row in enumerate(rows):
        require(type(row) is dict, 'route metadata')
        integers = {'route': route, 'provider_bytes': PROVIDER_SIZE, 'width': WIDTH, 'height': HEIGHT,
                    'image_stride': STRIDE, 'image_bits_per_component': 32, 'image_bits_per_pixel': 128,
                    'image_bitmap_info': 8449, 'stride': STRIDE, 'allocation_bytes': DEST_SIZE,
                    'bits_per_component': 32, 'bits_per_pixel': 128, 'bitmap_info': 8449}
        for key, expected in integers.items():
            require(type(row.get(key)) is int and row[key] == expected, 'typed metadata:' + key)
        require(type(row.get('pid')) is int and 1 < row['pid'] <= 2147483647, 'typed pid')
        pids.append(row['pid'])
        require(row.get('color_space') == 'kCGColorSpaceLinearSRGB', 'destination profile')
        require(row.get('source_color_space') == ('kCGColorSpaceLinearSRGB' if route else 'kCGColorSpaceSRGB'), 'source profile')
        for key, expected in [('provider_file', 'route%d-provider.raw' % route), ('file', 'route%d-readback.raw' % route)]:
            require(row.get(key) == expected, 'file binding')
            require(not (root / expected).is_symlink(), 'symlink')
        source = (root / row['provider_file']).read_bytes()
        actual = (root / row['file']).read_bytes()
        require(len(source) == PROVIDER_SIZE and source == provider, 'complete independent provider')
        require(len(actual) == DEST_SIZE, 'complete destination')
        require(row.get('provider_sha256') == digest(source) and row.get('sha256') == digest(actual), 'output digest')
        # Padding and tail are prerequisite integrity checks, never tolerated model residuals.
        for y in range(HEIGHT):
            require(actual[y * STRIDE + WIDTH * 16:(y + 1) * STRIDE] == b'\xa5' * 64, 'destination padding')
        require(actual[PROVIDER_SIZE:] == b'\xa5' * (DEST_SIZE - PROVIDER_SIZE), 'destination tail')
        outputs.append({'route': route, 'identity': byte_relation(actual, identity),
                        'historical_8bit_relation': byte_relation(actual, old[route])})
    require(pids[0] == pids[1], 'single producer pid')
    return {'native_acquisition_qualified': False, 'canvas_qualified': False,
            'scope': 'raw byte comparison; execution receipts and independent native review required',
            'provider_bytes_compared': 2 * PROVIDER_SIZE, 'readback_bytes_compared': 2 * DEST_SIZE,
            'all_bytes_compared': 2 * (PROVIDER_SIZE + DEST_SIZE),
            'readback_padding_bytes': 384, 'readback_tail_bytes': 24192,
            'linear_identity_control': outputs[1]['identity']['exact'], 'routes': outputs}

if __name__ == '__main__':
    import sys
    require(len(sys.argv) == 4, 'usage: compare.py RAW_ROOT STDOUT_JSONL HISTORICAL_ROOT')
    rows = [parsed(line) for line in Path(sys.argv[2]).read_text().splitlines()]
    print(json.dumps(compare(Path(sys.argv[1]), rows, anchored_old(sys.argv[3])), sort_keys=True))
