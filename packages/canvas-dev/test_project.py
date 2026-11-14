"""Tests of source adaptation and configuration, not native Canvas parity."""
import tempfile,unittest
from pathlib import Path
from project import code_mask,preview_snapshot,jsonc,resolve_source,select_factory,strip_preview_blocks
from server import Session

class Tests(unittest.TestCase):
    def test_entry_attribute_preserves_literals_comments_and_offsets(self):
        source='// @main\n/* nested /* @main */ comment */\nlet s = #"@main"#\n@main struct App {}\n'
        result,count=preview_snapshot(source)
        self.assertEqual(count,1);self.assertEqual(len(result),len(source));self.assertIn('#"@main"#',result);self.assertIn('      struct App',result)
        self.assertEqual(result.count('\n'),source.count('\n'))

    def test_trailing_comma_parser_preserves_quoted_punctuation(self):
        self.assertEqual(jsonc('{"v": ",]", "a": [1,],}'),{'v':',]','a':[1]})

    def test_project_selects_factory_and_tracks_other_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);project=root/'Demo.xcodeproj';project.mkdir();source=root/'Sources';source.mkdir()
            a=source/'Main.swift';a.write_text('@main struct Demo {}\nfunc makePreview() {}');b=source/'Model.swift';b.write_text('struct Model {}')
            (project/'project.xcproj').write_text('{"targets":[{"name":"Demo"}],"files":[{"kind":"folder","path":"Sources","target-membership":["Demo"]}],}')
            primary,extras,metadata=resolve_source(project,'makePreview');self.assertEqual(primary,a.resolve());self.assertEqual(extras,[b.resolve()])
            session=Session(primary,root/'work',factory='makePreview',extra_sources=extras,project=metadata)
            before=session.read_inputs()[2];b.write_text('struct NewModel {}');self.assertNotEqual(before,session.read_inputs()[2]);session.close()
            self.assertIn('@main',a.read_text())

    def test_project_refresh_discovers_added_removed_files_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();project=root/'Demo.xcodeproj';project.mkdir();sources=root/'Sources';sources.mkdir()
            primary=sources/'View.swift';primary.write_text('func makePreview() {}')
            manifest=project/'project.xcproj'
            value={'targets':[{'name':'Demo'}],'files':[{'kind':'folder','path':'Sources','target-membership':['Demo']}],'build-settings':{'SWIFT_VERSION':'5.0'}}
            import json
            manifest.write_text(json.dumps(value));bound,extras,metadata=resolve_source(project,'makePreview')
            session=Session(bound,root/'work',factory='makePreview',extra_sources=extras,project=metadata)
            try:
                original=session.read_inputs()[2];added=sources/'New.swift';added.write_text('struct New {}')
                inputs=session.read_inputs();self.assertNotEqual(original,inputs[2]);self.assertEqual([p for p,_ in inputs[3]],[added])
                added.unlink();self.assertEqual(session.read_inputs()[2],original)
                value['build-settings']['SWIFT_VERSION']='6.0';manifest.write_text(json.dumps(value));self.assertNotEqual(session.read_inputs()[2],original);self.assertEqual(session.project['swift_version'],'6')
                manifest.write_text('{partial')
                with self.assertRaises(ValueError):session.read_inputs()
                manifest.write_text(json.dumps(value));self.assertEqual(session.read_inputs()[3],[])
                primary.write_text('struct Old {}');added.write_text('func makePreview() {}')
                with self.assertRaisesRegex(ValueError,'factory moved'):session.read_inputs()
                self.assertEqual(session.source,primary);self.assertEqual(primary.read_text(),'struct Old {}')
            finally:session.close()

    def test_malformed_project_shapes_reject_with_value_error(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp)/'Bad.xcodeproj';project.mkdir();manifest=project/'project.xcproj'
            for value in [[],{'targets':[{}]},{'targets':[1]},{'targets':[{'name':'T'}],'files':[1]},{'targets':[{'name':'T'}],'files':{} }]:
                manifest.write_text(json.dumps(value))
                with self.assertRaises(ValueError):resolve_source(project,'makePreview')

    def test_factory_snapshot_strips_balanced_preview_registration_only(self):
        text='func makePreview() {}\n// #Preview { ignored() }\n#Preview("Demo") { VStack { Text("}") } }\nlet keep = 4\n'
        result,count=strip_preview_blocks(text)
        self.assertEqual(count,1);self.assertEqual(len(result),len(text));self.assertIn('// #Preview { ignored() }',result);self.assertIn('func makePreview() {}',result);self.assertIn('let keep = 4',result)
        with self.assertRaises(ValueError):strip_preview_blocks('#Preview { Text("unfinished")')

    def test_file_factory_follows_one_plain_preview_without_guessing(self):
        source='func makeMyPreview() {}\n#Preview("Name") { makeMyPreview() }'
        self.assertEqual(select_factory(source,'makePreview'),'makeMyPreview')
        self.assertEqual(select_factory('struct RootView: View {}','RootView'),'RootView')
        self.assertEqual(select_factory('func makePreview() {}\n'+source,'makePreview'),'makePreview')
        for invalid in ['func wrong() {}','// #Preview { wrong() }\nfunc wrong() {}',source+'\nfunc other() {}\n#Preview { other() }']:
            with self.assertRaises(ValueError):select_factory(invalid,'missing')

    def test_settings_enforce_bounds_and_rebuild_on_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'View.swift';source.write_text('fixture');s=Session(source,root/'work')
            self.assertEqual(s.config['scale'],2);s.configure({'color_scheme':'dark'});self.assertEqual(s.force,1)
            s.configure({'color_scheme':'dark'});self.assertEqual(s.force,1)
            for invalid in [{'scale':True},{'scale':3},{'width':0},{'color_scheme':'auto'},{'chrome':'false'}]:
                with self.assertRaises(ValueError):s.configure(invalid)
            s.close()

if __name__=='__main__':unittest.main()
