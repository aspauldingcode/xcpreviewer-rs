#!/usr/bin/env python3
"""Compare RGBA images with explicit geometry/color limits; writes a diff PNG."""
import argparse
import json
import pathlib
from PIL import Image,ImageChops,ImageStat


def compare(reference,candidate,diff,threshold=0):
    if not 0<=threshold<=255:raise ValueError('threshold must be 0..255')
    with Image.open(reference) as source_a, Image.open(candidate) as source_b:
        a,b=source_a.copy(),source_b.copy()
    if a.size!=b.size: return {'comparable':False,'reason':'dimensions differ','reference_size':a.size,'candidate_size':b.size,'passed':False}
    if a.info.get('icc_profile')!=b.info.get('icc_profile'):
        return {'comparable':False,'reason':'ICC profiles differ; normalize explicitly before comparison','passed':False}
    a,b=a.convert('RGBA'),b.convert('RGBA')
    delta=ImageChops.difference(a,b);delta.save(diff)
    pixels=list(delta.getdata());changed=sum(max(pixel)>threshold for pixel in pixels)
    return {'comparable':True,'size':a.size,'threshold':threshold,'changed_pixels':changed,
            'changed_fraction':changed/len(pixels),'mean_absolute_error_rgba':ImageStat.Stat(delta).mean,
            'max_channel_error':max(max(p) for p in pixels),'passed':changed==0,
            'normalization':'RGBA conversion only; no resizing, profile conversion, font or scale normalization'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=pathlib.Path);p.add_argument('candidate',type=pathlib.Path)
    p.add_argument('--diff',type=pathlib.Path,required=True);p.add_argument('--threshold',type=int,default=0);a=p.parse_args()
    result=compare(a.reference,a.candidate,a.diff,a.threshold);print(json.dumps(result,indent=2));return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
