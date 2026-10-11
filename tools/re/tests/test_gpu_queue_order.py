import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('gpu_order_reader',Path(__file__).with_name('verify_gpu_queue_order.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class GpuQueueOrderTests(unittest.TestCase):
 def test_native_order_and_complete_allocations(self):self.assertEqual(reader.verify(ROOT/'research/evidence/gpu-queue-order-2026-10-11')['complete_bytes'],229376)
 def test_resealed_wait_event_early_writer_resource_stale_and_padding(self):
  for kind in ['wait','event','early-writer','resource','stale','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-queue-order-2026-10-11',e);p=e/'result-0.json';d=json.loads(p.read_text())
    if kind=='wait':(e/'wait-0.json').write_text(json.dumps({'code':1,'timeout':False,'stderr':''}))
    elif kind=='event':d['fresh']['event']=2
    elif kind=='early-writer':d['stale']['writer_calls']=1
    elif kind=='resource':d['resources_after'][0]+=16
    elif kind=='stale':d['fresh']['destination']=d['stale']['destination']
    else:
     b=bytearray(base64.b64decode(d['fresh']['destination']));b[44]^=1;d['fresh']['destination']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
