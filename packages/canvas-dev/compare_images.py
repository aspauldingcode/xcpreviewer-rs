#!/usr/bin/env python3
"""Compare captures in sRGB without stretching unequal layout proposals."""
from pathlib import Path
from PIL import Image, ImageCms, ImageChops
import argparse, io, json

def srgb(path):
    im=Image.open(path);profile=im.info.get('icc_profile');rgb=im.convert('RGB')
    if profile:rgb=ImageCms.profileToProfile(rgb,ImageCms.ImageCmsProfile(io.BytesIO(profile)),ImageCms.createProfile('sRGB'),outputMode='RGB')
    return rgb

def compare(reference,reconstruction,output):
    a,b=srgb(reference),srgb(reconstruction)
    if a.size!=b.size:raise ValueError('Equal pixel extents required; do not stretch differing layouts')
    diff=ImageChops.difference(a,b);metrics={}
    for name,box in [('whole',(0,0,a.width,a.height)),('content',(0,65,a.width,a.height))]:
        values=list(diff.crop(box).getdata());total=len(values);changed=sum(any(p) for p in values)
        metrics[name]={'pixels':total,'changed_pixels':changed,'exact_pixel_percent':100*(total-changed)/total,'mean_absolute_channel_error':sum(sum(p) for p in values)/(total*3),'maximum_channel_error':max(max(p) for p in values)}
    output.mkdir(parents=True,exist_ok=True)
    heat=diff.point(lambda v:min(255,v*8));heat.save(output/'difference-8x.png')
    sheet=Image.new('RGB',(a.width*3,a.height),'white');sheet.paste(a,(0,0));sheet.paste(b,(a.width,0));sheet.paste(heat,(a.width*2,0));sheet.resize((1800,400)).save(output/'comparison.png')
    metrics.update(size=list(a.size),color_space='sRGB; embedded profiles converted before comparison',content_crop_starts_at_row=65,difference_gain=8)
    (output/'comparison.json').write_text(json.dumps(metrics,indent=2)+'\n');return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('reconstruction',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(compare(a.reference,a.reconstruction,a.output),indent=2))
