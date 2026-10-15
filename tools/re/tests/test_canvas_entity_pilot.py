import unittest
from pathlib import Path
from canvas_entity_pilot import digest, extract_document, produce, validate_role

class EntityPilotRulesTests(unittest.TestCase):
    def test_event_requires_selected_timestamped_enumerated_kind(self):
        base=dict(context='A render completed.',identity='run-1:render-1')
        self.assertFalse(validate_role('Event',**base,event_kind='render'))
        self.assertFalse(validate_role('Event',**base,timestamp='2026-10-15T00:00:00Z',event_kind='mutation'))
        self.assertFalse(validate_role('Event',**base,timestamp='2026-10-15T00:00:00',event_kind='render'))
        self.assertTrue(validate_role('Event',**base,timestamp='2026-10-15T00:00:00Z',event_kind='render'))

    def test_group_context_rejects_singleton_even_with_identity(self):
        for kind, context in [('Resource','Each of two helpers creates an owned surface.'),('Session','Both processes exit.'),('Frame','baseline and repeat red'),('Event','Both request abort.')]:
            self.assertFalse(validate_role(kind,context=context,identity='invented-singleton',timestamp='2026-10-15T00:00:00Z',event_kind='request'))
        self.assertFalse(validate_role('Resource',context='A receive-only name retains its right.'))

    def test_unicode_spans_and_no_question_or_instruction_claim(self):
        raw='# Ω report\n\nDoes it work? Next: inspect the source.\n\nThe frame remains blue after a10ms turn.\n'.encode()
        records=extract_document(Path('report.md'),raw,digest(raw))
        self.assertEqual([r['proposed_type'] for r in records],['Evidence','Claim'])
        self.assertEqual(records[1]['surface_form'],'The frame remains blue after a10ms turn.')
        for row in records:
            self.assertEqual(raw.decode()[slice(*row['char_span'])],row['surface_form'])

    def test_pinned_bytes_fail_closed_and_short_input_not_padded(self):
        raw=b'# Tiny report\n\nNo result.\n'
        with self.assertRaises(ValueError):extract_document(Path('tiny.md'),raw,'0'*64)
        self.assertEqual(len(extract_document(Path('tiny.md'),raw,digest(raw))),1)

    def test_actual_development_sample_preserves_limits(self):
        root=Path(__file__).resolve().parents[3];result=produce(root)
        self.assertLessEqual(result['entity_predictions'],50)
        self.assertEqual(len({r['source_path'] for r in result['candidates']}),10)
        self.assertEqual({r['proposed_type'] for r in result['candidates']},{'Evidence','Claim'})
        self.assertFalse(result['quality_gate_passed']);self.assertIsNone(result['precision'])
        self.assertTrue(result['development_set_reuse']);self.assertFalse(result['held_out'])
        self.assertEqual(result['accepted_graph_edges'],[])
        for row in result['candidates']:
            raw=(root/row['source_path']).read_bytes()
            self.assertEqual(digest(raw),row['source_sha256'])
            self.assertEqual(raw.decode()[slice(*row['char_span'])],row['surface_form'])


class DocumentaryRelationTests(unittest.TestCase):
    def setUp(self):
        import json
        self.root=Path(__file__).resolve().parents[3]
        self.raw=(self.root/'research/canvas-reviews/typed-pilot-v2-2026-10-15.json').read_bytes()
        self.review_raw=(self.root/'research/canvas-reviews/typed-pilot-v2-independent-review-2026-10-15.json').read_bytes()
        self.review=json.loads(self.review_raw)

    def test_actual_forty_deterministic_documentary_edges(self):
        from canvas_entity_pilot import documentary_relations
        a=documentary_relations(self.root,self.raw,self.review_raw)
        self.assertEqual(a,documentary_relations(self.root,self.raw,self.review_raw))
        self.assertEqual(a['relation_predictions'],40)
        self.assertEqual({e['relation'] for e in a['candidates']},{'ASSERTS'})
        self.assertFalse(a['truth_entailment']);self.assertFalse(a['quality_gate_passed'])
        self.assertEqual(a['accepted_graph_edges'],[])

    def test_missing_rejected_or_repaired_endpoint_review_fails(self):
        import copy,json
        from canvas_entity_pilot import documentary_relations
        for fault in ['missing','reject','repair','type','source_check','original','independent','proposition']:
            with self.subTest(fault=fault):
                review=copy.deepcopy(self.review);row=review['rows'][1]
                if fault=='missing':review['rows'].pop()
                elif fault=='reject':row['verdict']='reject'
                elif fault=='repair':row['repair_applied']=True
                elif fault=='type':row['type_fit']=False
                elif fault=='source_check':row['checks']['hash']=False
                elif fault=='original':row['original_prediction']['source_sha256']='0'*64
                elif fault=='independent':review['reviewer_context']=review['producer_context']
                else:row['explicit_proposition_fit']=False
                raw=json.dumps(review).encode()
                with self.assertRaises(ValueError):documentary_relations(self.root,self.raw,raw,digest(raw))

    def test_review_pin_candidate_hash_and_domain_range_fail_closed(self):
        import json,tempfile
        from canvas_entity_pilot import documentary_relations
        with self.assertRaises(ValueError):documentary_relations(self.root,self.raw,self.review_raw+b' ')
        with self.assertRaises(ValueError):documentary_relations(self.root,self.raw+b' ',self.review_raw)
        original=json.loads((self.root/'research/loop/canvas-ontology.json').read_text())
        for bad in [{'domain':['Claim']},{'range':['Evidence']},{'truth_entailment':True}]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'research/loop').mkdir(parents=True)
                ontology=json.loads(json.dumps(original));ontology['relations']['ASSERTS'].update(bad)
                (root/'research/loop/canvas-ontology.json').write_text(json.dumps(ontology))
                with self.assertRaises(ValueError):documentary_relations(root,self.raw,self.review_raw)


class BoundedClaimLimitTests(unittest.TestCase):
    def test_invalid_limits_fail_at_both_entrypoints(self):
        root=Path(__file__).resolve().parents[3]
        raw=b'# Tiny report\n\nThe frame remains blue throughout the retained comparison.\n'
        for invalid in [True,False,0,-1,9,1000000,1.5,'5',None]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):produce(root,invalid)
                with self.assertRaises(ValueError):extract_document(Path('tiny.md'),raw,digest(raw),invalid)

    def test_default_is_exact_original_v2_and_extended_sample_deterministic(self):
        import json
        root=Path(__file__).resolve().parents[3]
        original=json.loads((root/'research/canvas-reviews/typed-pilot-v2-2026-10-15.json').read_bytes())
        self.assertEqual(produce(root),original)
        self.assertEqual(produce(root,4),original)
        extended=produce(root,5,generation='v3')
        self.assertEqual(extended,produce(root,5,generation='v3'))
        self.assertEqual(len(extended['candidates']),60)
        self.assertTrue(all(row['id'].startswith('typed-pilot-v3-') for row in extended['candidates']))
        for path in {r['source_path'] for r in original['candidates']}:
            old=[r['surface_form'] for r in original['candidates'] if r['source_path']==path]
            new=[r['surface_form'] for r in extended['candidates'] if r['source_path']==path]
            self.assertEqual(new[:len(old)],old)
        with self.assertRaises(ValueError):produce(root,5,generation='v999')

    def test_short_document_not_padded_at_maximum(self):
        raw=b'# Short report\n\nThe frame remains blue throughout the retained comparison.\n'
        rows=extract_document(Path('short.md'),raw,digest(raw),8)
        self.assertEqual(len(rows),2)
        self.assertEqual([r['proposed_type'] for r in rows],['Evidence','Claim'])
