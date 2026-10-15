import hashlib,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
from verify_reentrant_file import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/reentrant-file-observation-2026-10-14'
class ReentrantFileTests(unittest.TestCase):
 def test_sealed_controls(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'13d58a153a91eb02a586ab26eaea26764addfa1c736ef811ba617b82aa72b922')
  self.assertEqual(verify(E)['full_frame_bytes'],65536)
  self.assertEqual(hashlib.sha256((E/'after.js').read_bytes()).hexdigest(),'933f8646b7a52f27aaf120250869629f6a9a9d9f5bb10d81c6725ca7f7f4ac73')
  with tempfile.TemporaryDirectory() as tmp:
   fresh=Path(tmp)/'e';fresh.mkdir();(fresh/'after.js').write_bytes((ROOT/'tools/re/reloop/source_file_loop.js').read_bytes())
   for mode in ['poll','refresh']:
    out=Path(tmp)/mode
    subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/reentrant_file_control.js'),str(fresh),'after',mode,str(out)],capture_output=True,check=True,timeout=8)
    self.assertEqual(json.loads((out/'result.json').read_text()),json.loads((E/('after-'+mode)/'result.json').read_text()))
 def test_resealed_faults(self):
  for fault in range(10):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'after-refresh/result.json';d=json.loads(p.read_text())
    if fault==0:d['winner']=0
    elif fault==1:d['builds']=[0,1,0]
    elif fault==2:d['aborts']=0
    elif fault==3:d['events'][-1]['generation']=4
    elif fault==4:d['events'][-1]['sourceSha256']='0'*64
    elif fault==5:d['finalStatus']['liveWorkers']=1
    elif fault==6:p=e/'before-poll/result.json';d=json.loads(p.read_text());d['winner']=2
    elif fault==7:p=e/'after-poll-wait.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'after-refresh/frame.raw';b=bytearray(p.read_bytes());b[52 if fault==8 else 16383]^=1;p.write_bytes(b);d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
