import json
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.core import Controller, ROOT, atomic, digest, load, validate_queue
from reloop.evidence import Store, artifact, claim, page
from reloop.responses import bounded, page as response_page
from reloop.verification import bytes_equal, typed, sealed_compare
from reloop.swiftmeta import MachO
from reloop.canvas import select_tab, workspace, compare_captures, switch_scheme
from reloop.planner import plan


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.c = Controller(root=self.root)

    def seal(self, name='run-one', execution='success', observed=None):
        run = self.c.runs / name
        (run / 'output').mkdir(parents=True)
        atomic(run / 'output/result.json', {'observations': observed or {'calls': 6}})
        atomic(run / 'manifest.json', {'run_id': name, 'sealed': True,
            'execution': execution, 'verdict': 'supports', 'environment_hash': 'test-environment',
            'artifacts': self.c.artifacts(run)})
        return run

    def test_scheme_switch_changes_only_marked_value_and_reverses(self):
        source = 'unmarked .environment(\\.colorScheme, .dark)\n' + '.environment(\\.colorScheme, .dark) // RE_SCHEME_SWITCH\n'
        light = switch_scheme(source, 'light')
        self.assertEqual(light, source.replace('.dark) // RE_SCHEME_SWITCH', '.light) // RE_SCHEME_SWITCH'))
        self.assertEqual(switch_scheme(light, 'dark'), source)
        self.assertEqual(switch_scheme(source, 'dark'), source)

    def test_scheme_switch_rejects_ambiguous_or_missing_marker(self):
        marker = '.environment(\\.colorScheme, .dark) // RE_SCHEME_SWITCH'
        for text, value in [('', 'light'), (marker * 2, 'light'), (marker, 'automatic')]:
            with self.assertRaises(ValueError): switch_scheme(text, value)

    def test_exact_compare_detects_bit_flip_and_tail(self):
        a, b = self.root/'a', self.root/'b'
        a.write_bytes(b'\x00\xff'); b.write_bytes(b'\x01\xfe\x00')
        r = bytes_equal(a, b)
        self.assertFalse(r['passed'])
        self.assertEqual((r['different_bytes'], r['different_bits_in_shared_extent'], r['unmatched_tail_bytes']), (3, 2, 1))
        self.assertEqual(r['first_mismatches'][-1], {'offset': 2, 'reference': None, 'candidate': 0})

    def test_exact_compare_crosses_stream_boundary(self):
        a, b = self.root/'a', self.root/'b'
        a.write_bytes(b'a'*65537); b.write_bytes(b'a'*65536+b'b')
        self.assertEqual(bytes_equal(a, b)['first_mismatches'][0]['offset'], 65536)
        b.write_bytes(a.read_bytes()); self.assertTrue(bytes_equal(a, b)['passed'])

    def test_typed_comparison_preserves_signed_zero_and_bool(self):
        self.assertNotEqual(typed(-0.0), typed(0.0))
        self.assertNotEqual(typed(True), typed(1))
        self.assertEqual(typed({'b': 2, 'a': 1}), typed({'a': 1, 'b': 2}))

    def test_external_anchor_detects_rewritten_manifest_and_artifact(self):
        run = self.seal(); anchor = digest(run/'manifest.json')
        self.assertTrue(self.c.verify(run.name, anchor)['valid'])
        atomic(run/'output/result.json', {'observations': {'calls': 999}})
        m = load(run/'manifest.json'); m['artifacts'] = self.c.artifacts(run)
        atomic(run/'manifest.json', m)
        # A self-consistent rewrite is only detectable against an independent anchor.
        self.assertTrue(self.c.verify(run.name)['valid'])
        self.assertFalse(self.c.verify(run.name, anchor)['valid'])

    def test_sealed_comparison_refuses_tampered_input(self):
        run = self.seal(); ref = {'run_id': run.name, 'path': 'output/result.json'}
        self.assertTrue(sealed_compare(self.c, ref, ref)['passed'])
        (run/'output/result.json').write_text('changed')
        with self.assertRaises(RuntimeError): sealed_compare(self.c, ref, ref)

    def test_comparison_detects_evidence_changed_during_read(self):
        run = self.seal(); ref = {'run_id': run.name, 'path': 'output/result.json'}
        def racing(a, b):
            result = bytes_equal(a, b)
            pathlib.Path(a).write_text('changed during comparison')
            return result
        with patch('reloop.verification.bytes_equal', side_effect=racing):
            with self.assertRaisesRegex(RuntimeError, 'changed during comparison'):
                sealed_compare(self.c, ref, ref)

    def test_artifact_traversal_and_unsealed_files_rejected(self):
        run = self.seal()
        for path in ['../manifest.json', '/etc/hosts', 'manifest.json']:
            with self.assertRaises(ValueError): artifact(self.c, run.name, path)
        with self.assertRaises(ValueError): self.c.verify('..')

    def test_search_quarantines_tampered_evidence(self):
        run = self.seal(); store = Store(self.c); self.addCleanup(store.close)
        self.assertEqual(store.index()['runs'], 1)
        self.assertEqual(len(store.search('calls')), 1)
        (run/'output/result.json').write_text('{}')
        self.assertEqual(store.search('calls'), [])
        self.assertEqual(store.index()['invalid'], [run.name])
        self.assertEqual(store.db.execute('SELECT count(*) FROM nodes').fetchone()[0], 0)

    def test_claim_separates_failed_tool_from_counterevidence(self):
        good = self.seal(); failed = self.seal('run-failed', 'failed')
        spec = {'id': 'six-calls', 'assertion': 'Six calls observed.', 'scope': 'Owned fixture only.',
                'evidence': [{'run_id': good.name, 'check': {'path': 'calls', 'equals': 6}}]}
        self.assertEqual(claim(self.c, spec)['status'], 'supported')
        spec['evidence'][0]['check']['equals'] = 7
        self.assertEqual(claim(self.c, spec)['status'], 'contradicted')
        spec['evidence'][0]['run_id'] = failed.name
        self.assertEqual(claim(self.c, spec)['status'], 'candidate')

    def test_large_compacted_response_retains_exact_original(self):
        original = {'base64': 'X'*20000, 'values': list(range(400))}
        r = bounded(self.c, original)
        self.assertLess(len(json.dumps(r)), 6500)
        chunks = []; offset = 0
        while offset is not None:
            p = response_page(self.c, r['response_id'], offset, 1000)
            chunks.append(p['text']); offset = p['next_offset']
        self.assertEqual(json.loads(''.join(chunks)), original)
        (self.c.state/'responses'/(r['response_id']+'.json')).write_text('{}')
        with self.assertRaises(RuntimeError): response_page(self.c, r['response_id'])

    def test_run_specific_graph_preserves_shared_function_identity(self):
        for name in ['run-one', 'run-two']:
            run = self.seal(name)
            atomic(run/'output/joined-trace.json', {'links': [{'image_sha256': 'same', 'offset': '0x4'}]})
            m = load(run/'manifest.json'); m['artifacts'] = self.c.artifacts(run); atomic(run/'manifest.json', m)
        store = Store(self.c); self.addCleanup(store.close); store.index()
        for name in ['run-one', 'run-two']:
            self.assertEqual(sum(n['kind']=='function' for n in store.graph(name)['nodes']), 1)

    def test_canvas_selects_exact_owned_project(self):
        project = self.root/'PreviewLab.xcodeproj'
        message = '* tabIdentifier: other, workspacePath: /another/project\n* tabIdentifier: owned, workspacePath: '+str(project)+'\n'
        self.assertEqual(select_tab(message, project), 'owned')
        with self.assertRaises(RuntimeError): select_tab(message+message, project)

    def test_xcode_workspace_mutation_cannot_change_frozen_source(self):
        source=self.root/'source';source.mkdir()
        (source/'fixture.swift').write_text('original')
        (source/'xcuserdata').mkdir();(source/'xcuserdata/private').write_text('user state')
        clone=workspace(source,self.root/'workspaces')
        self.assertFalse((clone/'xcuserdata').exists())
        (clone/'fixture.swift').write_text('Xcode writes')
        self.assertEqual((source/'fixture.swift').read_text(),'original')

    def test_uncomparable_images_cannot_pass_repeatability_control(self):
        from PIL import Image
        from reloop.core import evaluate
        a,b=self.root/'a.png',self.root/'b.png'
        Image.new('RGBA',(2,2),'white').save(a);Image.new('RGBA',(3,2),'white').save(b)
        result=compare_captures([a,b],self.root)
        self.assertFalse(result['pixels_identical'])
        self.assertNotEqual(evaluate([{'path':'pixels_identical','equals':True}],{'observations':result})[0],'supports')

    def test_pixel_equality_does_not_claim_png_byte_equality(self):
        from PIL import Image,PngImagePlugin
        a,b=self.root/'a.png',self.root/'b.png';image=Image.new('RGBA',(2,2),'white')
        image.save(a);metadata=PngImagePlugin.PngInfo();metadata.add_text('test','different encoding metadata')
        image.save(b,pnginfo=metadata)
        result=compare_captures([a,b],self.root)
        self.assertTrue(result['pixels_identical']);self.assertFalse(result['preview_bytes_identical'])

    def test_repeatability_proposal_requires_positive_pixel_equality(self):
        run=self.seal(observed={'wire_capture_complete':False,'fixture_content_nonblank':True})
        atomic(run/'experiment.json',{'adapter':'xcode_preview','params':{'variants':[0,1]}})
        m=load(run/'manifest.json');m['artifacts']=self.c.artifacts(run);atomic(run/'manifest.json',m)
        atomic(self.c.state/'checkpoint.json',{'runs':{'canvas':run.name}})
        proposal=plan(self.c)['proposals'][0]
        self.assertIn({'path':'pixels_identical','equals':True},proposal['checks'])

    def test_planner_rejects_chrome_only_capture_readiness(self):
        run=self.seal(observed={'fixture_content_nonblank':False})
        atomic(run/'experiment.json',{'adapter':'xcode_preview','params':{'variants':[0,1]}})
        m=load(run/'manifest.json');m['artifacts']=self.c.artifacts(run);atomic(run/'manifest.json',m)
        atomic(self.c.state/'checkpoint.json',{'runs':{'canvas':run.name}})
        result=plan(self.c)
        self.assertEqual(result['proposals'],[])
        self.assertEqual(result['outcomes'][0]['action'],'diagnose-blank-owned-content')

    def test_macho_rejects_truncated_load_commands(self):
        path = self.root/'bad-macho'
        path.write_bytes(struct.pack('<8I', 0xfeedfacf, 0, 0, 0, 1, 8, 0, 0)+struct.pack('<II', 0x19, 72))
        with self.assertRaisesRegex(ValueError, 'Invalid load command'): MachO(path)

    def test_planner_quarantines_tamper_instead_of_proposing(self):
        run = self.seal()
        atomic(self.c.state/'checkpoint.json', {'runs': {'owned': run.name}})
        (run/'output/result.json').write_text('{}')
        result = plan(self.c)
        self.assertEqual(result['proposals'], [])
        self.assertEqual(result['outcomes'][0]['action'], 'quarantine')

    def test_planner_advances_xpc_counterexperiment_without_duplicate_proposal(self):
        run=self.seal(observed={'truncated_data_decodes_empty_dictionary':True})
        atomic(run/'experiment.json',{'adapter':'xpc_negative','params':{}})
        m=load(run/'manifest.json');m['artifacts']=self.c.artifacts(run);atomic(run/'manifest.json',m)
        atomic(self.c.state/'checkpoint.json',{'runs':{'owned-negative':run.name}})
        proposed=plan(self.c)
        self.assertEqual(proposed['proposals'][0]['id'],'xpc-prefix-boundary')
        atomic(self.root/'research/loop/campaign.json',{'experiments':proposed['proposals']})
        queued=plan(self.c)
        self.assertEqual(queued['proposals'],[])
        self.assertIn('run-reviewed-followup',[o['action'] for o in queued['outcomes']])

    def test_campaign_schema_matches_executor(self):
        import jsonschema
        queue = load(ROOT/'research/loop/campaign.json')
        validate_queue(queue)
        for e in queue['experiments']:
            jsonschema.validate(e, load(ROOT/'schemas/re-experiment.schema.json'))

    def test_published_native_goldens_preserve_typed_values_and_hashes(self):
        import plistlib
        root=ROOT/'tools/re/fixtures/PlistOracle'
        manifest=load(root/'manifest.json')
        self.assertEqual(len(manifest['fixtures']),3)
        for fixture in manifest['fixtures']:
            values=[]
            for key in ['input','reference']:
                path=root/fixture[key]['path']
                self.assertEqual(digest(path),fixture[key]['sha256'])
                self.assertEqual(path.stat().st_size,fixture[key]['bytes'])
                values.append(typed(plistlib.loads(path.read_bytes())))
            self.assertEqual(*values)

    def test_frozen_source_hashes_override_stale_live_scan(self):
        from test_core import experiment
        def fake(argv, directory, *args):
            atomic(directory/'output/result.json', {'observations': {'events': 6}})
            return {'execution': 'success', 'exit_code': 0, 'duration_seconds': 0}
        with patch('reloop.core.source_files', return_value=[ROOT/'tools/re/reloop/__init__.py']), \
                patch('reloop.core.execute', side_effect=fake):
            m = self.c.run_one(experiment(), {'tool_sources': {'stale': 'wrong'}})
        self.assertEqual(m['environment']['tool_sources'], m['tool_source_hashes'])
        self.assertNotIn('stale', m['environment']['tool_sources'])
        run=self.c.runs/m['run_id']
        self.assertTrue(self.c.verify(run.name)['valid'])
        (run/'source/tools/re/reloop/__init__.py').write_text('changed while running')
        m['artifacts']=self.c.artifacts(run);atomic(run/'manifest.json',m)
        self.assertFalse(self.c.verify(run.name)['frozen_sources_unchanged'])


if __name__ == '__main__': unittest.main()
