import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('restore_reader',Path(__file__).with_name('verify_mcp_restore.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpRestoreTests(unittest.TestCase):
 def test_missing_empty_same_source_restoration(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-restore-2026-10-11')['complete_bytes'],98304)
 def test_resealed_revision_generation_wait_and_padding(self):
  for kind in ['revision','generation','wait','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-restore-2026-10-11',e);p=e/'process/result.json';d=json.loads(p.read_text());row=d['records'][0]
    if kind=='wait':row['wait']['code']=1;(e/'process/restore/wait.json').write_text(json.dumps(row['wait']))
    else:
     for i in [7,9]:
      f=row['values'][i]['result']['structuredContent']['frame']
      if kind=='revision':f['descriptor']['revision']=1
      elif kind=='generation':f['descriptor']['generation']=1
      else:
       b=bytearray(base64.b64decode(f['allocationBase64']));b[52]^=1;f['allocationBase64']=base64.b64encode(b).decode();f['descriptor']['allocationSha256']=hashlib.sha256(b).hexdigest()
     for i in [6,8,10]:
      r=row['values'][i]['result'];status=json.loads(r['content'][0]['text']);status['frame']=row['values'][7]['result']['structuredContent']['frame']['descriptor'];status['readiness']['frameRevision']=status['frame']['revision'];r['content'][0]['text']=json.dumps(status)
    for item in row['wire']:
     if item['direction']=='receive' and item['message']['id']>=2:item['message']['result']=row['values'][item['message']['id']-2]['result']
    (e/'process/restore/partial.json').write_text(json.dumps({'wire':row['wire'],'values':row['values']}));p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
