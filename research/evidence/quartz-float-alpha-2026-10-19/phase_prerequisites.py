"""Fail-closed prerequisites for reviewed owned research probes.

Call guarded_dispatch while holding the controller lock. This validates stored
receipts and current artifact identities; it does not authenticate hostile files,
prove unseen-process quiescence, or establish native Canvas behavior.
"""
import hashlib
import json
import math
import re
from pathlib import Path


class PrerequisiteRejected(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise PrerequisiteRejected(reason)


def integer(value, expected=None):
    return type(value) is int and (expected is None or value == expected)


def parsed(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise PrerequisiteRejected('Nonfinite JSON constant')

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

    def finite(item):
        if type(item) is float:
            require(math.isfinite(item), 'Nonfinite JSON number')
        elif type(item) is dict:
            for child in item.values():
                finite(child)
        elif type(item) is list:
            for child in item:
                finite(child)
    finite(value)
    return value


def read(root, name):
    path = root / name
    require(path.is_file() and not path.is_symlink(), 'Missing or linked receipt')
    require(path.stat().st_size <= 262144, 'Oversize receipt')
    return parsed(path.read_text())


def digest(path):
    require(path.is_file() and not path.is_symlink(), 'Missing or linked artifact')
    require(path.stat().st_size <= 67108864, 'Oversize artifact')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(root, phase, source_hash, binary_hash):
    outer = read(root, phase + '-outer.json')
    require(integer(outer['node_exit'], 0), 'Guard process failed')
    row = read(root, phase + '-record.json')
    require(row['phase'] == phase, 'Wrong phase')
    require(row['source_sha256'] == source_hash and
            row['binary_sha256'] == binary_hash, 'Artifact binding changed')
    require(row['error'] is None, 'Guard error')
    record = row['record']
    report = record['report']
    require(report['kind'] == 'complete' and integer(report['target_code'], 0)
            and report['failure'] is None and report['drained'] is True
            and integer(report['remaining_observed'], 0), 'Incomplete observed lifecycle')
    require(record['emergencyClosed'] is False and
            record['privateAbortRequested'] is False, 'Aborted guard')
    require(type(record['stdout']) is str and type(record['stderr']) is str,
            'Invalid captured streams')
    raw = record['stdout'].encode()
    require(len(raw) <= 131072 and integer(record['stdoutBytes'], len(raw))
            and record['stdoutSha256'] == hashlib.sha256(raw).hexdigest(),
            'Captured output changed')
    err = record['stderr'].encode()
    require(len(err) <= 131072 and integer(record['stderrBytes'], len(err))
            and record['stderrSha256'] == hashlib.sha256(err).hexdigest(),
            'Captured diagnostics changed')
    if phase == 'output-valid':
        require(row['args'] == ['--output-control', 'output-valid'], 'Wrong control args')
        markers = re.findall(r'^owned_tree_pid:([1-9][0-9]*)$', record['stderr'], re.M)
        require(len(markers) == 1, 'Missing or ambiguous owned PID')
        pid = int(markers[0])
        require(1 < pid <= 2147483647, 'Invalid owned PID')
        output = parsed(raw)
        require(type(output) is dict and set(output) == {'pid', 'status'}
                and integer(output['pid'], pid) and output['status'] == 'owned_output_control',
                'Output control rejected')
    return row


def guarded_dispatch(root, phase, launch):
    """Validate dependencies before invoking launch; exceptions never invoke it.

    Caller owns exclusive lock, reviewed pin validation and fixed deadline inside
    launch. This function does not obtain a second lock or replenish any budget.
    """
    require(phase in ('compile', 'output-valid', 'fixture'), 'Unknown phase')
    root = Path(root)
    if phase != 'compile':
        source_hash = digest(root / 'probe.swift')
        binary_hash = digest(root / 'probe')
        receipt(root, 'compile', source_hash, binary_hash)
        if phase == 'fixture':
            receipt(root, 'output-valid', source_hash, binary_hash)
    return launch()
