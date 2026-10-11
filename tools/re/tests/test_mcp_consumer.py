import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('consumer_reader',Path(__file__).with_name('verify_mcp_consumer.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpConsumerTests(unittest.TestCase):
 def test_real_publication_race_and_consumer_guards(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-consumer-2026-10-11')['complete_bytes'],147456)
 def test_resealed_sample_race_wait_and_padding(self):
  for kind in ['sample','race','wait','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-consumer-2026-10-11',e);p=e/'process/result.json';d=json.loads(p.read_text());row=d['records'][0]
    if kind=='sample':row['samples'][3]['status']['frame']['revision']=1
    elif kind=='race':row['values'][10]['result']=row['values'][13]['result']
    elif kind=='wait':row['wait']['code']=1;(e/'process/consumer/wait.json').write_text(json.dumps(row['wait']))
    else:
     for i in [12,15,19]:
      f=row['values'][i]['result']['structuredContent']['frame'];b=bytearray(base64.b64decode(f['allocationBase64']));b[44]^=1;f['allocationBase64']=base64.b64encode(b).decode();f['descriptor']['allocationSha256']=hashlib.sha256(b).hexdigest()
     for i in [11,13,14,16,17,18,20]:
      r=row['values'][i]['result'];s=json.loads(r['content'][0]['text']);s['frame']=row['values'][15]['result']['structuredContent']['frame']['descriptor'];r['content'][0]['text']=json.dumps(s)
     for sample,si,fi in zip(row['samples'],[2,6,9,16,20,24],[1,5,8,15,19,23]):sample.update(status=json.loads(row['values'][si]['result']['content'][0]['text']),frame=row['values'][fi]['result']['structuredContent']['frame'])
    for item in row['wire']:
     if item['direction']=='receive' and item['message']['id']>=2:item['message']['result']=row['values'][item['message']['id']-2]['result']
    (e/'process/consumer/partial.json').write_text(json.dumps({'wire':row['wire'],'values':row['values']}));p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
