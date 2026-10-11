"""Separate update-result reflection and direct-tag witness projection, static only."""
import struct
from reloop.discriminants import instructions
from reloop.statepattern import checked_body
from reloop.tokendescriptor import span
from reloop.chained import rebase
from reloop.tokenlink import branch
from reloop.tokenconsume import signed
from reloop.stubbind import inspect as inspect_stub

BODIES = {
    0x2e860: (0x2e8f8, '41c195be17ee6de99e9767f61728f2a5319bece7152628057d602de98134deaf'),
    0x2e8f8: (0x2e9e0, '299593e1737d47f2d3eb9b5388a4f0346ed1034aefd3820f5e33417e1e2d55cb'),
    0x2e054: (0x2e0f8, 'dfd78711fc8f7e3afe7274c66bfd4ff8b281ddbaf4e124bdb12d537537fef5d0'),
    0x2de9c: (0x2df24, '6064540d3c963128ae3acbf581f58b7b7d876c1f2b7f2a062a79fce48cafb488'),
}
IMPORTS = {0x1311f8: '_swift_checkMetadataState', 0x1313e4: '_swift_initEnumMetadataMultiPayload'}


def project(source, size_a, size_b, tag):
    if any(type(v) is not int or not 0 <= v <= 4096 for v in (size_a, size_b)):
        raise ValueError('Bounded result payload sizes required')
    if type(tag) is not int or tag not in (0, 1):
        raise ValueError('Only direct result tags accepted')
    offset = max(size_a, size_b)
    if len(source) <= offset:
        raise ValueError('Missing result tag byte')
    result = bytearray(source)
    result[offset] = tag
    return bytes(result), offset, 24 if tag == 1 else 32


def conditional(word, site, target, condition):
    if word & 0xff00001f != 0x54000000 | condition or site + 4 * signed((word >> 5) & 0x7ffff, 19) != target:
        raise ValueError('Result direct-tag branch changed')


def inspect(texts, image):
    bodies = {}
    for text in texts:
        start = min(instructions(text))
        if start in bodies:
            raise ValueError('Duplicate result witness entry')
        bodies[start] = text
    if set(bodies) != set(BODIES) | set(IMPORTS):
        raise ValueError('Exact result witness/import set required')
    codes = {start: checked_body(bodies[start], image, start, stop, h) for start, (stop, h) in BODIES.items()}
    d = 0x150928
    context = image.context(d)
    if context['kind'] != 18 or context['name'] != 'WaitingStateUpdateResult' or context.get('parent', {}).get('name') != 'FulfillOnceState':
        raise ValueError('Wrong separate result context')
    if image.unpack('<12I', image.file_offset(d)) != (0xd2, 0xffffff7c, 0xfffe38b0, 0xffedc6a0, 0x781c, 0x05000002, 0, 0x36ffc, 0xfffe38b8, 3, 3, 0x808080):
        raise ValueError('Result generic descriptor changed')
    f = image.relative(d + 16)
    if f != 0x158154 or struct.unpack('<HHI', span(image, f + 8, 8)) != (2, 12, 2):
        raise ValueError('Result field bounds changed')
    names = [image.string(image.relative(f + 24 + 12 * i)) for i in range(2)]
    if names != ['updated', 'alreadyFulfilled']:
        raise ValueError('Result case names changed')
    if span(image, image.relative(f + 20), 5) != b'qd__\0' or span(image, image.relative(f + 32), 3) != b'q_\0':
        raise ValueError('Result payload type records changed')
    p = 0x134200
    if image.relative(d + 32) != p or span(image, p, 16) != struct.pack('<iiIi', 0x30a18 - p, 0x2de9c - (p + 4), 0x40200000, 0x173f88 - (p + 12)):
        raise ValueError('Independent result pattern bytes changed')
    slots = {0x173f90: 0x2e054, 0x173fe0: 0x2e860, 0x173fe8: 0x1e5c, 0x173ff0: 0x2e8f8}
    if any(rebase(image, a)['target'] != target for a, target in slots.items()):
        raise ValueError('Result witness association changed')
    selected = {
        0x2e860: {0x2e860: 0xa941a029, 0x2e878: 0x9a888129, 0x2e87c: 0x38696808, 0x2e880: 0x7100090a, 0x2e8f0: 0xaa0803e0, 0x2e8f4: 0xd65f03c0},
        0x2e8f8: {0x2e908: 0x7100043f, 0x2e910: 0xa941a448, 0x2e928: 0x9a898108, 0x2e92c: 0x38286801},
        0x2e054: {0x2e054: 0xa941a029, 0x2e074: 0x710009cd, 0x2e0e4: 0x710005df, 0x2e0e8: 0x9a8a016a, 0x2e0ec: 0x9a880121, 0x2e0f0: 0xf9400542, 0x2e0f4: 0xd61f0040},
        0x2de9c: {0x2deb0: 0xf9401001, 0x2ded0: 0xf9400e61, 0x2defc: 0x52800042},
    }
    if any(codes[start][site][2] != word for start, words in selected.items() for site, word in words.items()):
        raise ValueError('Result size/tag/destroy dataflow changed')
    conditional(codes[0x2e860][0x2e884][2], 0x2e884, 0x2e8f0, 3)
    conditional(codes[0x2e8f8][0x2e90c][2], 0x2e90c, 0x2e934, 8)
    conditional(codes[0x2e054][0x2e078][2], 0x2e078, 0x2e0e4, 3)
    if branch(codes[0x2e8f8][0x2e930][2], 0x2e930, False) != 0x2e9d0:
        raise ValueError('Result direct injector exit changed')
    for site, target in [(0x2deb8, 0x1311f8), (0x2ded8, 0x1311f8), (0x2df00, 0x1313e4)]:
        if branch(codes[0x2de9c][site][2], site, True) != target:
            raise ValueError('Result completer import call changed')
    for address, name in IMPORTS.items():
        inspect_stub(bodies[address], image, address, name, '/usr/lib/swift/libswiftCore.dylib')
    cases = compared = 0
    for a in range(257):
        for b in range(257):
            offset = a if a >= b else b
            source = bytes([0xa5]) * (offset + 5)
            for tag in (0, 1):
                actual, observed, metadata = project(source, a, b, tag)
                expected = source[:offset] + bytes([tag]) + source[offset + 1:]
                if actual != expected or observed != offset or metadata != {0: 32, 1: 24}[tag] or actual[offset] != tag:
                    raise ValueError('Result direct-tag/padding model contradicted')
                cases += 1
                compared += len(actual)
    return {'result_witness_verified': True, 'body_instruction_bytes_compared': 684, 'import_instruction_bytes_compared': 24, 'reflected_cases': names, 'named_case_indices_verified': False, 'witness_rebases_verified': 4, 'pattern_bytes_independently_compared': 16, 'payload_record_bytes_independently_compared': 8, 'direct_tag_model_cases': cases, 'whole_buffer_model_bytes_compared': compared, 'padding_bytes_per_buffer': 4, 'tag_offset': 'max(sizeA,sizeB)', 'destroy_metadata_offsets': {'0': 32, '1': 24}, 'scope': 'Separate result reflection, generic pattern and declared witness bodies; finite direct numeric tags only. Reflection order is not independent named case-index proof. No live result, payload validity, native witness invocation, extended-tag acceptance, runtime release/race or Canvas transport claim.'}
