import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('close_revision_reader',Path(__file__).with_name('verify_mcp_close_revision.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CloseRevisionTests(unittest.TestCase):
 def test_closed_revision_rejection_and_recovery(self):
  e=ROOT/'research/evidence/mcp-close-revision-2026-10-11';self.assertEqual((ROOT/'tools/re/reloop/preview_consumer.js').read_bytes(),(e/'runtime/preview_consumer.js').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],163840)
 def test_resealed_verdict_recovery_bytes_wait_and_runtime(self):
  for kind in ['verdict','recovery','padding','wait','runtime']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-close-revision-2026-10-11',e);p=e/'result.json';d=json.loads(p.read_text())
    if kind=='verdict':d['outcomes'][0]['rejected']=False
    elif kind=='recovery':d['outcomes'][0]['recoveryCalls']=0
    elif kind=='padding':
     b=bytearray(base64.b64decode(d['outcomes'][0]['afterAllocationBase64']));b[44]^=1;d['outcomes'][0]['afterAllocationBase64']=base64.b64encode(b).decode()
    elif kind=='wait':(e/'runtime-wait.json').write_text(json.dumps({'code':1,'timeout':False,'stderr':''}))
    else:shutil.copyfile(e/'baseline/preview_consumer.js',e/'runtime/preview_consumer.js')
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
