import base64
import contextlib
import pathlib
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.rawcoder import assess,CLASSES,KEYS,DATA,semantic
from reloop.canvas import frida_deadline,Monitor


def record(data=DATA):
    encoded=base64.b64encode(data).decode()
    return {'outcome':'decoded','decoded_base64':encoded,'matches_requested_class':True,'xpc_tree':{'type':'dictionary','count':1,'items':{'data':{'type':'data','bytes':len(data),'base64':encoded}}}}


def matrix():
    results={'data-'+cls+'-'+key:record() for cls in CLASSES for key in KEYS}
    for cls in CLASSES:
        for key in KEYS:results['data-'+cls+'-'+key]['matches_requested_class']=cls in ('NSData','NSObject')
    for mode in ('string','number','bool','array','dictionary'):results[mode+'-NSData-owned']={'outcome':'exception','phase':'encode','name':'NSInvalidArgumentException'}
    for mode in ('empty-data','nil','missing','wrong-wire-type'):results[mode+'-NSData-owned']={'outcome':'nil'}
    results['overwrite-NSData-owned']=record(b'second');return results


class RawCoderTests(unittest.TestCase):
    def test_class_and_key_controls_require_exact_actual_payloads(self):
        results=matrix();r=assess(results)
        self.assertEqual(r['exact_data_controls'],18);self.assertEqual(r['class_mismatch_returns_data'],12)
        self.assertEqual(r['nondata_encode_exceptions'],5);self.assertTrue(r['overwrite_returns_last_data'])
        results['data-NSString-owned']['decoded_base64']=base64.b64encode(b'altered').decode()
        self.assertEqual(assess(results)['exact_data_controls'],17)
        self.assertEqual(assess(results)['class_mismatch_returns_data'],11)

    def test_extra_wire_keys_and_integer_flags_do_not_pass(self):
        results=matrix();results['data-NSString-owned']['matches_requested_class']=0
        self.assertEqual(assess(results)['class_mismatch_returns_data'],11)
        results['data-NSData-owned']['xpc_tree']['items']['owned']={}
        self.assertEqual(assess(results)['exact_data_controls'],17)
        results['overwrite-NSData-owned']['xpc_tree']['items']['data']['bytes']=True
        self.assertFalse(assess(results)['overwrite_returns_last_data'])

    def test_replay_ignores_addresses_but_keeps_wire_and_exception_phase(self):
        a={'reason':'instance 0x1','outcome':'exception','name':'X','phase':'encode'}
        b={**a,'reason':'instance 0x2'};self.assertEqual(semantic(a),semantic(b))
        b['phase']='decode';self.assertNotEqual(semantic(a),semantic(b))

    def test_frida_cancellation_interrupts_blocking_operation(self):
        class Cancellation:
            def __init__(self):self.cancelled=threading.Event()
            def cancel(self):self.cancelled.set()
            def __enter__(self):return self
            def __exit__(self,*args):pass
        cancellation=Cancellation()
        with frida_deadline(.02,lambda:cancellation):
            self.assertTrue(cancellation.cancelled.wait(1))

    def test_cleanup_detaches_even_when_unload_raises(self):
        class Script:
            def unload(self):raise RuntimeError('unload failed')
        class Session:
            detached=False
            def detach(self):self.detached=True
        session=Session()
        import tempfile,json
        with tempfile.TemporaryDirectory() as temporary:
            m=Monitor(pathlib.Path(temporary),pathlib.Path(temporary));m.thread=unittest.mock.Mock()
            m.thread.is_alive.return_value=False;m.sessions={1:(session,Script()),2:(session,None)}
            with patch('reloop.canvas.frida_deadline',lambda _:contextlib.nullcontext()):m.close()
            self.assertTrue(session.detached)
            events=json.loads((pathlib.Path(temporary)/'preview-lifecycle.json').read_text())['events']
            self.assertEqual(events[0]['kind'],'cleanup-error')


if __name__=='__main__':unittest.main()
