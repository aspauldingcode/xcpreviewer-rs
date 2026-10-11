"""Fresh-process mechanical verification of a graph-loop experiment.

This verifies artifacts and recomputes the declared checks. It deliberately does
not certify an independent scientific review or delivery contract coverage.
"""
import argparse
import json
from reloop.core import Controller, canonical_hash, evaluate, load, validate_experiment


def verify(controller, run_id, anchor, experiment_hash):
    integrity = controller.verify(run_id, anchor)
    run = controller.runs / run_id
    manifest = load(run / 'manifest.json', {})
    spec = load(run / 'experiment.json', {})
    validate_experiment(spec)
    verdict, checks = evaluate(spec['checks'], load(run / 'output/result.json', {}))
    valid = (integrity['valid'] is True
             and integrity['external_anchor_matches'] is True
             and canonical_hash(spec) == experiment_hash == manifest.get('experiment_hash')
             and manifest.get('execution') == 'success'
             and manifest.get('verdict') == verdict == 'supports'
             and manifest.get('checks') == checks)
    return {'valid': valid, 'integrity': integrity, 'recomputed_verdict': verdict,
            'checks': checks, 'delivery_review': 'review-pending',
            'scope': 'Fresh-process artifact integrity and predeclared checks; not independent contract review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--anchor', required=True)
    parser.add_argument('--experiment-hash', required=True)
    args = parser.parse_args()
    try:
        result = verify(Controller(args.root, args.state_dir), args.run_id,
                        args.anchor, args.experiment_hash)
    except Exception as error:
        result = {'valid': False, 'error': str(error), 'delivery_review': 'review-pending'}
    print(json.dumps(result))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
