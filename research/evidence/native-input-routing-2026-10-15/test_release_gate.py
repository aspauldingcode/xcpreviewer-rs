import unittest
import tempfile
from pathlib import Path
from release_gate import may_release
class ReleaseGateTests(unittest.TestCase):
    root='/owned/fixture'
    user='/user/Project.xcodeproj'
    def check(self,text):return may_release(text,self.root,[self.user])
    def test_owned_remains_rejects(self):
        self.assertFalse(self.check('* tabIdentifier: windowtab11, workspacePath: /owned/fixture/PreviewLab.xcodeproj\n'))
    def test_user_only_admits(self):
        self.assertTrue(self.check('* tabIdentifier: windowtab12, workspacePath: '+self.user+'\n'))
    def test_owned_and_user_rejects(self):
        self.assertFalse(self.check('* tabIdentifier: windowtab11, workspacePath: /owned/fixture/PreviewLab.xcodeproj\n* tabIdentifier: windowtab12, workspacePath: '+self.user+'\n'))
    def test_empty_or_malformed_rejects(self):
        for text in ['',None,'No workspace windows found','unknown response']:
            self.assertFalse(self.check(text))
    def test_duplicate_tabs_rejects(self):
        self.assertFalse(self.check(('* tabIdentifier: windowtab12, workspacePath: '+self.user+'\n')*2))
    def test_missing_original_user_workspace_rejects(self):
        self.assertFalse(self.check('* tabIdentifier: windowtab13, workspacePath: /other/Project.xcodeproj\n'))
    def test_exact_owned_root_rejects(self):
        self.assertFalse(self.check('* tabIdentifier: windowtab11, workspacePath: /owned/fixture\n* tabIdentifier: windowtab12, workspacePath: '+self.user))
    def test_duplicate_slash_path_rejects(self):
        self.assertFalse(self.check('* tabIdentifier: windowtab11, workspacePath: /owned//fixture/P.xcodeproj\n* tabIdentifier: windowtab12, workspacePath: '+self.user))
    def test_noncanonical_root_and_empty_baseline_reject(self):
        message='* tabIdentifier: windowtab12, workspacePath: '+self.user
        self.assertFalse(may_release(message,'/owned/fixture/../fixture',[self.user]))
        self.assertFalse(may_release('No workspace windows found',self.root,[]))
    def test_symlink_to_owned_root_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';root.mkdir();project=root/'P.xcodeproj';project.mkdir()
            alias=Path(directory)/'alias';alias.symlink_to(root,target_is_directory=True)
            message='* tabIdentifier: windowtab11, workspacePath: '+str(alias/'P.xcodeproj')+'\n* tabIdentifier: windowtab12, workspacePath: '+self.user
            self.assertFalse(may_release(message,str(root),[self.user]))
if __name__=='__main__':unittest.main()
