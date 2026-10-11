import copy
import tempfile
import unittest
from pathlib import Path
from fractions import Fraction
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from reloop.extentcli import project_rgba,check_png
from reloop.core import ROOT,load,validate_experiment

class ExtentCliTests(unittest.TestCase):
    def test_projection_half_up_and_transparent_dirty_rgb(self):
        config={'width':1,'height':1}
        for alpha in (0,1,3,127,128,254,255):
            for value in (0,alpha//2,alpha):
                p=bytes((value,value,value,alpha));raw=p+b'\xa5'*12+b'\xc3'*(16384-16)
                want=0 if not alpha else int(Fraction(value*255,alpha)+Fraction(1,2))
                self.assertEqual(project_rgba(raw,config,16),bytes((want,want,want,alpha)))
        raw=bytes((255,128,1,0))+b'\xc3'*16380
        self.assertEqual(project_rgba(raw,config,4),bytes(4))
        with self.assertRaises(ValueError):project_rgba(bytes(16383),config,4)
    def test_png_pixels_format_dimensions_and_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'frame.png';cfg={'width':1,'height':1};info=PngInfo();info.add(b'sRGB',b'\0')
            image=Image.frombytes('RGBA',(1,1),bytes((85,0,0,3)));image.save(path,pnginfo=info)
            self.assertTrue(check_png(path,cfg,bytes((85,0,0,3)))['passed'])
            self.assertFalse(check_png(path,cfg,bytes((86,0,0,3)))['passed'])
            with self.assertRaises(ValueError):check_png(path,{'width':2,'height':1},bytes(8))
            image.save(path)
            with self.assertRaises(ValueError):check_png(path,cfg,bytes(4))
            image.convert('RGB').save(path,pnginfo=info)
            with self.assertRaises(ValueError):check_png(path,cfg,bytes(4))
    def test_typed_exclusive_mode(self):
        base=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='primary-source-frame-native-extents')
        validate_experiment(base)
        for value in (1,'true',None):
            e=copy.deepcopy(base);e['params']['extent_cli_control']=value
            with self.assertRaises(ValueError):validate_experiment(e)
        e=copy.deepcopy(base);e['params']['source_cli_control']=True
        with self.assertRaises(ValueError):validate_experiment(e)
