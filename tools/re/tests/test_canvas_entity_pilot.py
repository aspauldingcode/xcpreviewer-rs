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
