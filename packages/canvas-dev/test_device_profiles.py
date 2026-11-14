"""Synthetic catalog checks; actual installed geometry is recorded separately."""
import unittest,tempfile,plistlib
from pathlib import Path
from device_profiles import load_profiles

class Tests(unittest.TestCase):
 def test_declared_canvas_controls_layout_not_blind_physical_pixel_division(self):
  with tempfile.TemporaryDirectory() as directory:
   resources=Path(directory)/'iPhone Fixture.simdevicetype/Contents/Resources';resources.mkdir(parents=True)
   (resources/'profile.plist').write_bytes(plistlib.dumps({}))
   display=dict(deviceName='primary',width=1080,height=2340,canvasWidth=1125,canvasHeight=2436,scale=3)
   (resources/'capabilities.plist').write_bytes(plistlib.dumps({'capabilities':{'displays':[display]}}))
   profiles,assets=load_profiles(Path(directory));profile=profiles['iPhone Fixture:primary']
   self.assertEqual([profile['point_width'],profile['point_height']],[375,812]);self.assertEqual([profile['framebuffer_width'],profile['framebuffer_height']],[1080,2340]);self.assertEqual(assets,{})
 def test_no_installed_catalog_keeps_explicit_desktop(self):
  with tempfile.TemporaryDirectory() as directory:
   profiles,assets=load_profiles(Path(directory));self.assertEqual(list(profiles),['desktop']);self.assertEqual(assets,{})

if __name__=='__main__':unittest.main()
