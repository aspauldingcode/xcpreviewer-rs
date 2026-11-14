"""Owned child transport tests, not SwiftUI or private Xcode input parity."""
import tempfile,unittest,sys,stat
from pathlib import Path
from live_host import NativeHost

class Tests(unittest.TestCase):
 def helper(self,root,wrong=False):
  path=root/'helper';path.write_text('#!'+sys.executable+'\n'+'''import json,sys,pathlib,time
root=pathlib.Path(sys.argv[4]);(root/'frame.bplist').write_bytes(b'fixture frame')
for line in sys.stdin:
 value=json.loads(line)
 answer=json.dumps(dict(ok=True,id='''+('999' if wrong else 'value["id"]')+'''))+'\\n'
 sys.stdout.write('owned fixture output\\n');sys.stdout.flush()
 sys.stdout.write('XCPV');sys.stdout.flush();time.sleep(.01)
 sys.stdout.write('JSON:'+answer);sys.stdout.flush()
''');path.chmod(path.stat().st_mode|stat.S_IXUSR);return path
 def test_fragmented_reply_sequence_and_child_cleanup(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);host=NativeHost(self.helper(root),root/'work',10,10,2);process=host.process
   try:
    first,data=host.request('capture');second,_=host.request('capture')
    self.assertEqual([first['id'],second['id']],[1,2]);self.assertEqual(data,b'fixture frame');self.assertEqual(len(host.logs),2)
   finally:host.close()
   self.assertIsNotNone(process.poll());self.assertFalse((root/'work').exists())
   with self.assertRaisesRegex(RuntimeError,'closed'):host.request('capture')
 def test_wrong_sequence_is_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);host=NativeHost(self.helper(root,wrong=True),root/'work',10,10,2)
   try:
    with self.assertRaisesRegex(RuntimeError,'sequence'):host.request('capture')
   finally:host.close()

if __name__=='__main__':unittest.main()
