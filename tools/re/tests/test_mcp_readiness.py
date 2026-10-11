import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('readiness_reader',Path(__file__).with_name('verify_mcp_readiness.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpReadinessTests(unittest.TestCase):
 def test_first_rejection_recovery_and_historical_failure(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-readiness-2026-10-11')['complete_bytes'],65536)
 def test_resealed_current_state_generation_wait_and_padding(self):
  for kind in ['history','generation','wait','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-readiness-2026-10-11',e);p=e/'process/result.json';d=json.loads(p.read_text());row=d['records'][0]
    if kind=='history':
     r=row['values'][3]['result'];status=json.loads(r['content'][0]['text']);status['readiness']['state']='failed';r['content'][0]['text']=json.dumps(status);row['wire'][12]['message']['result']=r
    elif kind=='wait':row['wait']['code']=1;(e/'process/recovery/wait.json').write_text(json.dumps(row['wait']))
    else:
     for i in [4,6,8]:
      f=row['values'][i]['result']['structuredContent']['frame']
      if kind=='generation':f['descriptor']['generation']=1
      else:
       b=bytearray(base64.b64decode(f['allocationBase64']));b[52]^=1;f['allocationBase64']=base64.b64encode(b).decode();f['descriptor']['allocationSha256']=hashlib.sha256(b).hexdigest()
     for i in [3,5,7]:
      r=row['values'][i]['result'];status=json.loads(r['content'][0]['text']);status['frame']=row['values'][4]['result']['structuredContent']['frame']['descriptor'];r['content'][0]['text']=json.dumps(status)
    for item in row['wire']:
     if item['direction']=='receive' and item['message']['id']>=2:item['message']['result']=row['values'][item['message']['id']-2]['result']
    (e/'process/recovery/partial.json').write_text(json.dumps({'wire':row['wire'],'values':row['values']}));p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
