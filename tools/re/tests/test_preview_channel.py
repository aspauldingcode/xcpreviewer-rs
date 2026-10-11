import hashlib,importlib.util,json,shutil,tempfile,unittest,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('channel_reader',Path(__file__).with_name('verify_preview_channel.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class PreviewChannelTests(unittest.TestCase):
    def test_actual_frames_faults_and_fresh_stream_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/preview-channel-2026-10-11')['fault_controls'],9)
    def test_resealed_queue_suppression_and_packet_padding(self):
        for kind in ['queue','suppression','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/preview-channel-2026-10-11',folder);p=folder/'channel/result.json';d=json.loads(p.read_text())
                if kind=='queue':next(r for r in d['controls'] if r['name']=='queue-bound')['result']['cancelled']=0
                elif kind=='suppression':next(r for r in d['controls'] if r['name']=='close-pending')['packets'].append({'id':1,'ok':True,'result':{}})
                else:
                    packet=d['actual']['packets'][3]['result'];raw=bytearray(base64.b64decode(packet['allocationBase64']));raw[36]^=1;packet['allocationBase64']=base64.b64encode(raw).decode()
                p.write_text(json.dumps(d));(folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
                with self.assertRaises(AssertionError):reader.verify(folder)
