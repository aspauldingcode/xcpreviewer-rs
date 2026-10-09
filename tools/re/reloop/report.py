"""Produce a reviewed-summary candidate without copying raw captures or code."""
from reloop.core import load


def report(controller):
    records=[]
    for experiment,run_id in sorted(controller.status().get('runs',{}).items()):
        manifest=load(controller.runs/run_id/'manifest.json')
        valid=controller.verify(run_id)['valid']
        record={key:manifest.get(key) for key in ['run_id','experiment_id','hypothesis','execution','verdict','duration_seconds','started_at','finished_at','experiment_hash','environment_hash','controller_loaded_source_sha256']}
        record['artifact_hashes_valid']=valid
        record['checks']=manifest.get('checks',[])
        # Checks may contain user text in future experiments. This is a review
        # candidate; publication remains an explicit file-list/diff operation.
        records.append(record)
    return {'scope':'Local toolkit validation. Owned synthetic traces and native reference rendering are not a live Xcode canvas protocol capture.',
            'runs':records,'all_hashes_valid':all(r['artifact_hashes_valid'] for r in records),
            'all_hypotheses_supported':bool(records) and all(r['execution']=='success' and r['verdict']=='supports' for r in records)}
