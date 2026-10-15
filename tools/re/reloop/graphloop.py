"""Bounded, resumable execution of explicitly bound research tasks.

One lock owns selection, execution and checkpoint writes. Shared campaign and
acceptance policy remain unchanged. Successful scoped experiments are overlaid
from the local ledger; delivery acceptance always comes from the existing policy.
"""
import copy
import json
import math
import pathlib
import subprocess
import sys
import time
import uuid

from reloop.core import (atomic, canonical_hash, digest, identity, load, now,
                         tree_size, validate_queue)
from reloop.workgraph import build

DEFAULT_CONFIG = 'research/loop/graph-runner.json'


def configuration(controller):
    config = load(controller.root / DEFAULT_CONFIG)
    if not config or config.get('schema_version') != 1:
        raise ValueError('Graph runner configuration missing or unsupported')
    limits = config['limits']
    for key, maximum in [('rounds', 4), ('experiments', 4), ('artifact_bytes', 1073741824)]:
        if type(limits.get(key)) is not int or not 1 <= limits[key] <= maximum:
            raise ValueError('Invalid graph budget: ' + key)
    minutes = limits.get('minutes')
    if type(minutes) not in (int, float) or not math.isfinite(minutes) or not 0 < minutes <= 15:
        raise ValueError('Invalid graph time budget')
    mode = config['communication']
    if mode.get('skill') != 'caveman' or mode.get('intensity') != 'full':
        raise ValueError('Graph loop requires Caveman FULL')
    path = pathlib.Path(mode['path']).expanduser()
    if not path.is_file() or digest(path) != mode['sha256']:
        raise ValueError('Caveman skill missing or changed; reconcile configured identity')
    # The reasoning agent receives the actual pinned skill, not only a mode label.
    # This canonical adapter is already registered and has its own reviewed runner.
    # Preserve explicit user bindings (including an empty list) and all limits.
    if DEFAULT_CONFIG == 'research/loop/graph-runner.json':
        live = 'primary-live-wasm-swap'
        registered = load(controller.root / 'research/loop/live-swap-runner.json', {})
        policy = load(controller.root / 'research/loop/workgraph.json', {})
        queue = load(controller.root / 'research/loop/campaign.json', {})
        if (registered.get('schema_version') == 1
                and registered.get('task_bindings', {}).get(live) == [live]
                and any(t.get('id') == live for t in policy.get('research_tasks', []))
                and any(e.get('id') == live and e.get('adapter') == 'live_swap'
                        for e in queue.get('experiments', []))):
            config = copy.deepcopy(config)
            config['task_bindings'].setdefault(live, [live])
    return config, {'skill': 'caveman', 'intensity': 'full', 'path': str(path),
                    'sha256': mode['sha256'], 'instructions': path.read_text(),
                    'code_and_docs': 'normal precise language'}


def trusted(controller, run_id, anchor):
    try:
        result = controller.verify(run_id, anchor)
        return result.get('valid') is True and result.get('external_anchor_matches') is True
    except (ValueError, OSError, KeyError):
        return False


def independently_accepted(controller, graph):
    """A mechanical experiment verdict alone cannot terminate delivery work."""
    if not graph['all_milestones_complete']:
        return False
    policy = load(controller.root / 'research/loop/workgraph.json')
    checkpoint = load(controller.root / 'research/loop/continuous.json')
    anchors = {r['run_id']: r['manifest_sha256'] for r in checkpoint.get('recent_evidence', [])}
    for node in graph['nodes']:
        if node['kind'] != 'delivery':
            continue
        attestation = policy['acceptance_attestations'].get(node['id'], {})
        review = attestation.get('independent_review', {})
        rid, path = review.get('run_id'), review.get('path')
        if not rid or not path or pathlib.PurePosixPath(path).is_absolute() or '..' in pathlib.PurePosixPath(path).parts:
            return False
        if rid not in attestation.get('runs', []) or rid not in anchors or not trusted(controller, rid, anchors[rid]):
            return False
        manifest = load(controller.runs / rid / 'manifest.json', {})
        if path not in {a['path'] for a in manifest.get('artifacts', [])}:
            return False
        report = load(controller.runs / rid / path, {})
        rows = report.get('coverage', [])
        coverage_path = attestation.get('coverage_path')
        if not coverage_path or pathlib.PurePosixPath(coverage_path).is_absolute() or '..' in pathlib.PurePosixPath(coverage_path).parts:
            return False
        if coverage_path not in {a['path'] for a in manifest.get('artifacts', [])}:
            return False
        coverage = load(controller.runs / rid / coverage_path, {})
        required = coverage.get('required_checks', [])
        if (not isinstance(required, list) or not required or not all(isinstance(k, str) and k for k in required)
                or len(required) != len(set(required)) or not isinstance(rows, list)
                or any(not isinstance(row, dict) or not isinstance(row.get('id'), str) for row in rows)
                or {row.get('id') for row in rows} != set(required) or len(rows) != len(required)
                or report.get('coverage_path') != coverage_path):
            return False
        if (report.get('issue') != node['id'] or report.get('independent') is not True
                or not isinstance(report.get('reviewer_id'), str) or not report['reviewer_id'].strip()
                or report.get('verdict') != 'accepted' or not rows
                or any(row.get('accepted') is not True for row in rows)):
            return False
    return True


def overlay(controller, ledger, config):
    policy = copy.deepcopy(load(controller.root / 'research/loop/workgraph.json'))
    checkpoint = copy.deepcopy(load(controller.root / 'research/loop/continuous.json'))
    anchors = {r['run_id']: r for r in checkpoint.get('recent_evidence', [])}
    quarantined = {r['run_id'] for r in checkpoint.get('quarantined_evidence', [])}
    queue = load(controller.root / 'research/loop/campaign.json')
    specs = {e['id']: e for e in queue['experiments']}
    for task in policy['research_tasks']:
        completed = []
        covered = set()
        required = config['task_bindings'].get(task['id'], [])
        for record in ledger.get('accepted', {}).get(task['id'], []):
            rid = record['run_id']
            eid = record['experiment_id']
            if eid not in required or eid not in specs or record['experiment_hash'] != canonical_hash(specs[eid]):
                continue
            if rid in quarantined:
                continue
            # Never overwrite a conflicting separately retained anchor.
            if rid in anchors and anchors[rid]['manifest_sha256'] != record['manifest_sha256']:
                continue
            if not trusted(controller, rid, record['manifest_sha256']):
                continue
            anchors[rid] = {'run_id': rid, 'manifest_sha256': record['manifest_sha256']}
            completed.append(rid)
            covered.add(eid)
        if required and covered == set(required):
            task['completion_runs'] = sorted(set(task.get('completion_runs', []) + completed))
    checkpoint['recent_evidence'] = list(anchors.values())
    return policy, checkpoint


def failure_key(task, experiments, environment):
    return canonical_hash({'task': task['id'], 'experiments': experiments,
                           'prerequisites': task.get('requires_runs', []),
                           'environment': environment})


def frontier(controller, config, ledger, environment):
    queue = validate_queue(load(controller.root / 'research/loop/campaign.json'))
    experiments = {e['id']: e for e in queue['experiments']}
    policy, checkpoint = overlay(controller, ledger, config)
    graph = build(controller, policy=policy, checkpoint=checkpoint)
    known = {t['id'] for t in graph['research_frontier']}
    if set(config['task_bindings']) - known:
        raise ValueError('Unknown graph task binding')
    candidates = []
    for task in graph['research_frontier']:
        if task['state'] != 'ready':
            continue
        ids = config['task_bindings'].get(task['id'], [])
        if not ids:
            candidates.append({'task': task['id'], 'state': 'reviewed-binding-required'})
            continue
        if (not isinstance(ids, list) or not all(isinstance(eid, str) for eid in ids)
                or len(ids) != len(set(ids))):
            raise ValueError('Invalid graph task experiment binding')
        if any(eid not in experiments for eid in ids):
            raise ValueError('Unknown bound experiment for ' + task['id'])
        allowed = task.get('completion_experiment_ids', [task['id']])
        if set(ids) - set(allowed):
            raise ValueError('Experiment outside task completion scope')
        specs = [experiments[eid] for eid in ids]
        fingerprint = failure_key(task, specs, environment)
        failure = ledger.get('failures', {}).get(task['id'])
        if failure and failure['fingerprint'] == fingerprint:
            candidates.append({'task': task['id'], 'state': 'changed-prerequisite-required',
                               'fingerprint': fingerprint})
            continue
        # Successful runs retained before interruption need not be executed again.
        prior = {e['experiment_id'] for e in ledger.get('accepted', {}).get(task['id'], [])
                 if e['experiment_hash'] in {canonical_hash(s) for s in specs}
                 and trusted(controller, e['run_id'], e['manifest_sha256'])}
        pending = [s for s in specs if s['id'] not in prior]
        if not pending:
            candidates.append({'task': task['id'], 'state': 'evidence-reconciliation-required'})
            continue
        ready = {e['id'] for e in controller.ready(queue, controller.status(), environment)}
        pending = [s for s in pending if s['id'] in ready]
        if not pending:
            candidates.append({'task': task['id'], 'state': 'experiment-prerequisite-required'})
            continue
        candidates.append({'task': task['id'], 'issue': task['issue'], 'scope': task['scope'],
                           'state': 'ready', 'fingerprint': fingerprint,
                           'experiment': pending[0]})
    return graph, candidates


def inspect(controller):
    config, communication = configuration(controller)
    ledger = load(controller.state / 'graph-loop.json', {'accepted': {}, 'failures': {}})
    graph, candidates = frontier(controller, config, ledger, identity())
    return {'communication': communication, 'candidates': candidates,
            'all_milestones_complete': independently_accepted(controller, graph),
            'execution_started': False, 'delivery_review': 'review-pending',
            'blocked_tasks': [{'task': t['id'], 'state': t['state'], 'blocker': t.get('blocker'),
                               'missing_evidence': t.get('missing_evidence', [])}
                              for t in graph['research_frontier']
                              if t['state'] in {'blocked', 'evidence-required'}]}


def fresh_verify(controller, manifest, seconds):
    argv = [sys.executable, '-m', 'reloop.loopverify', '--root', str(controller.root),
            '--state-dir', str(controller.state), '--run-id', manifest['run_id'],
            '--anchor', digest(controller.runs / manifest['run_id'] / 'manifest.json'),
            '--experiment-hash', manifest['experiment_hash']]
    result = subprocess.run(argv, cwd=controller.root / 'tools/re', capture_output=True,
                            text=True, timeout=max(0.01, min(seconds, 30)))
    value = json.loads(result.stdout)
    if result.returncode != 0:
        value['valid'] = False
    return value


def adopt_verified(controller, task_id, run_id, anchor):
    """Adopt scoped historical research only after fresh-process verification."""
    if (type(run_id) is not str or pathlib.Path(run_id).name != run_id
            or run_id in ('', '.', '..') or type(anchor) is not str
            or len(anchor) != 64 or any(c not in '0123456789abcdef' for c in anchor)):
        raise ValueError('Invalid adoption identity')
    with controller.lock():
        config, _ = configuration(controller)
        path = controller.state / 'graph-loop.json'
        ledger = load(path, {'schema_version': 1, 'accepted': {}, 'failures': {}, 'wakes': {}})
        if any(w.get('state') in ('running', 'reconciliation-required')
               for w in ledger.get('wakes', {}).values()):
            raise ValueError('Resume unfinished wake before adoption')
        checkpoint = load(controller.root / 'research/loop/continuous.json', {})
        if run_id in {r['run_id'] for r in checkpoint.get('quarantined_evidence', [])}:
            raise ValueError('Quarantined adoption run')
        for row in checkpoint.get('recent_evidence', []):
            if row['run_id'] == run_id and row['manifest_sha256'] != anchor:
                raise ValueError('Conflicting adoption anchor')
        policy = load(controller.root / 'research/loop/workgraph.json')
        task = next((t for t in policy['research_tasks'] if t['id'] == task_id), None)
        if task is None or not config['task_bindings'].get(task_id):
            raise ValueError('Reviewed adoption binding required')
        graph = build(controller, policy=policy, checkpoint=checkpoint)
        eligible = next((t for t in graph['research_frontier'] if t['id'] == task_id), None)
        if eligible is None or eligible['state'] not in ('ready', 'complete'):
            raise ValueError('Adoption research prerequisite unmet')
        folder = controller.runs / run_id
        manifest = load(folder / 'manifest.json', {})
        eid = manifest.get('experiment_id')
        allowed = task.get('completion_experiment_ids', [task_id])
        if eid not in config['task_bindings'][task_id] or eid not in allowed:
            raise ValueError('Adoption experiment outside task scope')
        queue = validate_queue(load(controller.root / 'research/loop/campaign.json'))
        spec = next((e for e in queue['experiments'] if e['id'] == eid), None)
        if (spec is None or manifest.get('run_id') != run_id
                or manifest.get('experiment_hash') != canonical_hash(spec)
                or manifest.get('execution') != 'success' or manifest.get('verdict') != 'supports'
                or digest(folder / 'manifest.json') != anchor):
            raise ValueError('Adoption contract or anchor changed')
        if tree_size(folder) > config['limits']['artifact_bytes']:
            raise ValueError('Adoption artifact budget exceeded')
        check = fresh_verify(controller, manifest, min(30, config['limits']['minutes'] * 60))
        report = {'task': task_id, 'run_id': run_id, 'manifest_sha256': anchor,
                  'experiment_id': eid, 'experiment_hash': manifest['experiment_hash'],
                  'verification': check, 'delivery_review': 'review-pending',
                  'scope': 'research-only', 'verified_at': now()}
        ledger.setdefault('adoptions', {})[task_id + ':' + run_id] = report
        if check.get('valid') is True:
            rows = ledger.setdefault('accepted', {}).setdefault(task_id, [])
            if not any(r['run_id'] == run_id for r in rows):
                rows.append({k: report[k] for k in ('run_id', 'manifest_sha256',
                                                   'experiment_id', 'experiment_hash')})
        atomic(path, ledger)
        if check.get('valid') is not True:
            raise ValueError('Fresh adoption verification failed; report retained')
        return report


def charge(controller, wake):
    for round_ in wake['rounds']:
        if round_.get('run_id'):
            round_['artifact_bytes'] = tree_size(controller.runs / round_['run_id'])
    wake['artifact_bytes'] = sum(r.get('artifact_bytes', 0) for r in wake['rounds'])
    wake['experiments'] = sum(bool(r.get('run_id')) for r in wake['rounds'])


def record(controller, ledger, round_, manifest, check):
    rid = manifest['run_id']
    round_.update(run_id=rid, verification=check,
                  execution=manifest.get('execution'), verdict=manifest.get('verdict'),
                  delivery_review='review-pending', finished_at=now())
    if check.get('valid') is True:
        round_['state'] = 'scoped-support'
        entry = {'run_id': rid, 'manifest_sha256': digest(controller.runs / rid / 'manifest.json'),
                 'experiment_id': manifest['experiment_id'],
                 'experiment_hash': manifest['experiment_hash']}
        rows = ledger['accepted'].setdefault(round_['task'], [])
        if rid not in {r['run_id'] for r in rows}:
            rows.append(entry)
    else:
        round_['state'] = 'failure-retained'
        prior = ledger['failures'].get(round_['task'], {})
        count = prior.get('count', 0) + 1 if prior.get('fingerprint') == round_['fingerprint'] else 1
        ledger['failures'][round_['task']] = {'fingerprint': round_['fingerprint'],
                                            'count': count, 'run_id': rid,
                                            'retry_requires': 'Changed relevant spec, prerequisite or environment'}


def run(controller, resume=None):
    config, communication = configuration(controller)
    path = controller.state / 'graph-loop.json'
    with controller.lock():
        boundary = load(controller.root / 'research/loop/continuous.json', {}).get('clean_room_boundary', {})
        if boundary.get('user_required') is True:
            raise ValueError('Clean-room boundary active: legacy execution bindings require scope/role review. Use tools/re/canvas_graph.py plan; inspection remains available. No wake or budget was created.')
        ledger = load(path, {'schema_version': 1, 'accepted': {}, 'failures': {}, 'wakes': {}})
        active = ledger.get('active_wake')
        if resume is None and active and ledger['wakes'][active]['state'] in {'running', 'reconciliation-required'}:
            resume = active
        if resume:
            if resume not in ledger['wakes']:
                raise ValueError('Unknown graph wake')
            wake = ledger['wakes'][resume]
            if wake['config_hash'] != canonical_hash(config):
                raise ValueError('Resume configuration changed; preserve original budget and reconcile')
        else:
            wake_id = uuid.uuid4().hex
            wake = {'id': wake_id, 'created_at': now(), 'deadline': time.time() + config['limits']['minutes'] * 60,
                    'config_hash': canonical_hash(config), 'limits': config['limits'],
                    'rounds': [], 'artifact_bytes': 0, 'experiments': 0, 'state': 'running',
                    'communication': communication}
            ledger['wakes'][wake_id] = wake
        if wake['state'] == 'reconciliation-required':
            return wake
        wake['state'] = 'running'
        ledger['active_wake'] = wake['id']
        atomic(path, ledger)
        controller.recover()
        # Recovery never re-runs a possibly executed pending experiment.
        for pending in wake['rounds']:
            if pending['state'] != 'running':
                continue
            ids = {p.name for p in controller.runs.iterdir()} - set(pending['before_runs'])
            matches = [load(controller.runs / rid / 'manifest.json', {}) for rid in ids]
            matches = [m for m in matches if m.get('experiment_hash') == pending['experiment_hash']]
            if len(matches) != 1:
                wake['state'] = 'reconciliation-required'
                atomic(path, ledger)
                return wake
            record(controller, ledger, pending, matches[0],
                   {'valid': False, 'error': 'Interrupted round requires explicit evidence review'})
        charge(controller, wake)
        attempted = {r['task'] for r in wake['rounds'] if r['state'] == 'failure-retained'}
        while (len(wake['rounds']) < wake['limits']['rounds']
               and wake['experiments'] < wake['limits']['experiments']
               and wake['artifact_bytes'] < wake['limits']['artifact_bytes']
               and time.time() < wake['deadline']):
            environment = identity()
            if time.time() >= wake['deadline']:
                break
            graph, candidates = frontier(controller, config, ledger, environment)
            if independently_accepted(controller, graph):
                wake['state'] = 'complete'
                break
            selected = next((c for c in candidates if c['state'] == 'ready' and c['task'] not in attempted), None)
            if not selected:
                wake.update(state='prerequisite-required', candidates=candidates,
                            blocked_tasks=[{'task': t['id'], 'state': t['state'], 'blocker': t.get('blocker'),
                                            'missing_evidence': t.get('missing_evidence', [])}
                                           for t in graph['research_frontier']
                                           if t['state'] in {'blocked', 'evidence-required'}])
                break
            spec = selected['experiment']
            round_ = {k: v for k, v in selected.items() if k != 'experiment'}
            round_.update(state='running', hypothesis=spec['hypothesis'], checks=spec['checks'],
                          experiment_hash=canonical_hash(spec), environment_hash=canonical_hash(environment),
                          before_runs=sorted(p.name for p in controller.runs.iterdir()), started_at=now())
            wake['rounds'].append(round_)
            atomic(path, ledger)
            try:
                manifest = controller.run_one(spec, environment, max(0.01, wake['deadline'] - time.time() - 5),
                                              wake['limits']['artifact_bytes'] - wake['artifact_bytes'])
                round_['run_id'] = manifest['run_id']
                atomic(path, ledger)
                try:
                    check = fresh_verify(controller, manifest, wake['deadline'] - time.time())
                except Exception as error:
                    check = {'valid': False, 'error': str(error)}
                record(controller, ledger, round_, manifest, check)
                cp = controller.status()
                cp.setdefault('runs', {})[spec['id']] = manifest['run_id']
                cp['updated_at'] = now()
                atomic(controller.state / 'checkpoint.json', cp)
                if check.get('valid') is not True:
                    attempted.add(selected['task'])
                charge(controller, wake)
                atomic(path, ledger)
            except BaseException:
                # Keep running capsule, original deadline and pre-execution run inventory.
                atomic(path, ledger)
                raise
        if wake['state'] == 'running':
            wake['state'] = 'budget-exhausted'
        wake['updated_at'] = now()
        atomic(path, ledger)
        return wake
