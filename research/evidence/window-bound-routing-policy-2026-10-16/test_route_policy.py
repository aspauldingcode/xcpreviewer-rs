from dataclasses import replace
import unittest
from route_policy import Window,decide,Denied
class RouteTests(unittest.TestCase):
    def setUp(self):
        self.a=Window(100,20,30,41,'/owned/a/PreviewLab.xcodeproj');self.root='/owned/a'
    def call(self,op='click',captured=None,current=None,**kw):
        return decide(op,captured or self.a,current or self.a,self.root,kw.get('ax',['AXPress']),kw.get('advertised',['CLICK']),kw.get('front',100),kw.get('hit',41),kw.get('element',self.a))
    def test_stable_bound_click_and_press_are_distinct(self):
        self.assertEqual(self.call(),'CLICK');self.assertEqual(self.call('press'),'PRESS')
    def test_click_only_element_never_becomes_axpress(self):
        self.assertEqual(self.call(ax=[]),'CLICK')
        with self.assertRaises(Denied):self.call('press',ax=[])
    def test_two_windows_same_control_label_reordered(self):
        b=replace(self.a,window_id=42,document='/owned/b/PreviewLab.xcodeproj')
        with self.assertRaises(Denied):self.call(current=b)
        with self.assertRaises(Denied):self.call(current=replace(self.a,window_id=42))
    def test_birth_document_and_pid_changes_reject(self):
        for b in [replace(self.a,pid=101),replace(self.a,birth_microseconds=31),replace(self.a,document='/owned/a/Sources/PreviewLab.swift')]:
            with self.assertRaises(Denied):self.call(current=b)
    def test_global_focus_and_hit_mismatch_reject(self):
        for kw in [{'front':200},{'hit':42},{'hit':None},{'advertised':[]}]:
            with self.assertRaises(Denied):self.call(**kw)
    def test_legacy_unbound_request_rejects(self):
        with self.assertRaises(Denied):decide('click',None,None,self.root,[],['CLICK'],100,41)
    def test_invalid_identity_and_paths_reject(self):
        for b in [replace(self.a,pid=True),replace(self.a,window_id=0),replace(self.a,birth_microseconds=1000000),replace(self.a,document='/owned//a/P.xcodeproj'),replace(self.a,document='/owned/a/../b/P.xcodeproj')]:
            with self.assertRaises(Denied):self.call(captured=b,current=b)
    def test_reviewer_malformed_capabilities_reject(self):
        for kw in [{'advertised':'NO_CLICK'}, {'ax':'NotAXPress'}, {'advertised':{'CLICK':True}}, {'ax':[None]}]:
            with self.assertRaises(Denied):self.call(**kw)
        with self.assertRaises(Denied):self.call('press',ax='NotAXPress')
    def test_reviewer_noninteger_observations_reject(self):
        for kw in [{'front':100.0},{'hit':41.0},{'front':True}]:
            with self.assertRaises(Denied):self.call(**kw)
    def test_reviewer_nul_path_rejects(self):
        b=replace(self.a,document='/owned/a/P\0.xcodeproj')
        with self.assertRaises(Denied):self.call(captured=b,current=b,element=b)
    def test_element_ancestor_binding_required(self):
        for b in [None,replace(self.a,window_id=42),replace(self.a,pid=101),replace(self.a,birth_seconds=21)]:
            with self.assertRaises(Denied):self.call('press',element=b)
            with self.assertRaises(Denied):self.call('click',element=b)
    def test_root_and_capability_bounds(self):
        for root in ['/', '/owned/a/', '//owned/a', '/owned/../owned/a', '/owned/a\0']:
            with self.assertRaises(Denied):decide('press',self.a,self.a,root,['AXPress'],[],element_window=self.a)
        for values in [[],['NO_CLICK'],['CLICK']*65,['CLICK','X'*65]]:
            with self.assertRaises(Denied):self.call(advertised=values)
if __name__=='__main__':unittest.main()
