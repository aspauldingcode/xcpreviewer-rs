"""Full dispatcher replay with synthetic clock/lock and mocked guard: no native launch."""
import contextlib,datetime,hashlib,io,json,runpy,shutil,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent
DEADLINE=datetime.datetime(2026,10,17,18,1,7,tzinfo=datetime.timezone.utc).timestamp()

def replay(original,delayed,phase):
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);pins=json.loads((P/'approved-pins.json').read_text())
  for n in pins:shutil.copyfile(P/n,p/n)
  if original:shutil.copyfile(P/'pre-lock-only-execute.py',p/'execute.py');pins['execute.py']=hashlib.sha256((p/'execute.py').read_bytes()).hexdigest()
  (p/'approved-pins.json').write_text(json.dumps(pins));(p/'probe').write_bytes(b'synthetic-not-executable')
  (p/'compile-record.json').write_text(json.dumps({'error':None,'record':{'report':{'target_code':0,'drained':True}},'binary_sha256':hashlib.sha256((p/'probe').read_bytes()).hexdigest()}))
  clock=[DEADLINE-200];calls=[]
  class Lock:
   def __enter__(self):clock[0]=DEADLINE+1 if delayed else DEADLINE-200
   def __exit__(self,*args):return False
  class Controller:
   def lock(self):return Lock()
  module=types.ModuleType('reloop.core');module.Controller=Controller
  def guard(*args,**kwargs):calls.append(True);return types.SimpleNamespace(returncode=0,stdout='',stderr='')
  code=0
  with patch.dict(sys.modules,{'reloop.core':module}),patch.object(sys,'argv',['execute.py',phase]),patch('time.time',side_effect=lambda:clock[0]),patch('subprocess.run',side_effect=guard),contextlib.redirect_stdout(io.StringIO()):
   try:runpy.run_path(str(p/'execute.py'),run_name='__main__')
   except SystemExit as e:code=e.code
  rejected=(p/(phase+'-after-lock-budget-rejection.json')).exists()
  return code,len(calls),rejected
class GateTests(unittest.TestCase):
 def test_before_deadline(self):
  for phase in ['compile','output-valid','fixture']:
   for original in [True,False]:
    with self.subTest(phase=phase,original=original):self.assertEqual(replay(original,False,phase),(0,1,False))
 def test_lock_delay(self):
  for phase in ['compile','output-valid','fixture']:
   with self.subTest(phase=phase):
    self.assertEqual(replay(True,True,phase),(0,1,False))
    self.assertEqual(replay(False,True,phase),(75,0,True))
if __name__=='__main__':unittest.main()
