import importlib.util,hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from jsonschema.exceptions import ValidationError
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('schema_reader',Path(__file__).with_name('verify_mcp_schema.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpSchemaTests(unittest.TestCase):
 def test_official_schema_falsification_and_fixed_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-schema-2026-10-11')['validated_native'],16)
 def test_resealed_null_id_tool_content_and_capability(self):
  for kind in ['id','content','capability']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    f=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-schema-2026-10-11',f);p=f/'after.json';d=json.loads(p.read_text())
    if kind=='id':d['handler']['malformed'][0]['id']=None
    elif kind=='content':d['handler']['packets'][6]['result']['content'][0]['type']='invalid'
    else:d['handler']['packets'][1]['result']['capabilities']['tools']=True
    p.write_text(json.dumps(d));(f/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(f)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in f.rglob('*') if p.is_file() and p!=f/'manifest.json'}}))
    with self.assertRaises((AssertionError,ValidationError)):reader.verify(f)
