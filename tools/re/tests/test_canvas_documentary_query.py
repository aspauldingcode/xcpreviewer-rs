import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import canvas_documentary_query as q

class DocumentaryQueryTests(unittest.TestCase):
    root=Path(__file__).resolve().parents[3]
    def test_reviewed_query_bounded_no_truth_promotion(self):
        data=q.load_reviewed(self.root);result=q.query(data,'refresh',2)
        self.assertEqual(len(result['results']),2);self.assertTrue(result['truncated'])
        self.assertFalse(result['truth_entailment']);self.assertFalse(result['native_acceptance'])
        self.assertFalse(result['global_graph_acceptance'])
        self.assertTrue(all(e['relation']=='ASSERTS' for r in result['results'] for e in r['documentary_edges']))
        for invalid in [True,0,21,-1]:
            with self.assertRaises(ValueError):q.query(data,'refresh',invalid)
        with self.assertRaises(ValueError):q.query(data,'')

    def test_exact_alias_fusion_keeps_provenance_and_separates_scope_grade(self):
        row=q.load_reviewed(self.root)['entities'][1];alias=copy.deepcopy(row);alias['id']='reviewed-alias'
        fused=q.fuse_entities([row,alias]);self.assertEqual(len(fused),1)
        self.assertEqual(fused[0]['original_ids'],[row['id'],'reviewed-alias'])
        self.assertEqual(len(fused[0]['provenance']),2)
        for attr in ['scope','source_grade','source_sha256','source_path']:
            changed=copy.deepcopy(alias);changed[attr]+='different'
            self.assertEqual(len(q.fuse_entities([row,changed])),2)
        for field in ['target_identity','target_version']:
            first=copy.deepcopy(row);second=copy.deepcopy(alias)
            first[field]='build-A';second[field]='build-B'
            groups=q.fuse_entities([first,second])
            self.assertEqual(len(groups),2)
            self.assertEqual([g[field] for g in groups],['build-A','build-B'])

    def test_changed_source_review_and_endpoint_fail_closed(self):
        original=Path.read_bytes
        source=q.load_reviewed(self.root)['entities'][0]['source_path']
        for target in [source,'research/canvas-reviews/'+q.NAMES[1],'research/canvas-reviews/'+q.NAMES[2]]:
            def changed(path,target=target):
                raw=original(path)
                return raw+b' ' if str(path).endswith(target) else raw
            with patch.object(Path,'read_bytes',changed):
                with self.assertRaises(ValueError):q.load_reviewed(self.root)

    def test_endpoint_tamper_rejected_even_with_changed_artifact_pin(self):
        original=Path.read_bytes;name=q.NAMES[2]
        document=json.loads(original(self.root/'research/canvas-reviews'/name))
        document['candidates'][0]['to']='absent-endpoint';raw=json.dumps(document).encode()
        def changed(path):
            return raw if str(path).endswith(name) else original(path)
        with patch.dict(q.PINS,{name:q.sha(raw)}),patch.object(Path,'read_bytes',changed):
            with self.assertRaises(ValueError):q.load_reviewed(self.root)
