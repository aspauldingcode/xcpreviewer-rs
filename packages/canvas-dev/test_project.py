"""Tests of source adaptation and configuration, not native Canvas parity."""
import tempfile,unittest
from pathlib import Path
from project import code_mask,preview_snapshot,jsonc,resolve_source
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

    def test_settings_enforce_bounds_and_rebuild_on_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'View.swift';source.write_text('fixture');s=Session(source,root/'work')
            self.assertEqual(s.config['scale'],2);s.configure({'color_scheme':'dark'});self.assertEqual(s.force,1)
            s.configure({'color_scheme':'dark'});self.assertEqual(s.force,1)
            for invalid in [{'scale':True},{'scale':3},{'width':0},{'color_scheme':'auto'},{'chrome':'false'}]:
                with self.assertRaises(ValueError):s.configure(invalid)
            s.close()

if __name__=='__main__':unittest.main()
