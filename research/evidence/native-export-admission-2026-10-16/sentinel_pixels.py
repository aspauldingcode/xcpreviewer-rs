"""Scoped owned sentinel pixel checks, independent of text glyph rasterization."""
from pathlib import Path
from PIL import Image
import hashlib
import json

def check(raw, size, mode):
    if size != (320,200) or len(raw)!=320*200*4 or mode not in ('dark','light'):
        return False
    background=(255,0,255,255) if mode=='dark' else (0,255,0,255)
    colors=set()
    for n in range(320*200):
        r,g,b,a=raw[n*4:n*4+4];colors.add((r,g,b,a))
        if a!=255 or (mode=='dark' and (g!=0 or r!=b)) or (mode=='light' and (r!=0 or b!=0)):
            return False
        x=n%320;y=n//320
        if (x<8 or x>=312 or y<8 or y>=192) and (r,g,b,a)!=background:
            return False
    return len(colors)>1

def main():
    if not __debug__:
        raise RuntimeError('Python optimization disables verifier checks')
    root=Path(__file__).parent
    expected={'dark.png': '7eb758bc299b9cae30ff8124f881c716e71b97e3840d82af446cc2e3a89750b4', 'recovered-light.png': 'bef2890dbee73115d10e4b3a4baa3744d2279f15aa75fb99e37488d81e86ca97', 'analysis.json': '01cafd47c724694cac911f7deb905b5badfc0c43c5dbebb043be462350276f2f', 'AppearanceSentinel.swift': 'c22219a49b3baafa47388898c35c4f131bb7a4aeb5ac7fe301508d63f78f8ddc'}
    for name,digest in expected.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Pinned input changed: '+name)
    p=root/'analysis.json';rows=json.loads(p.read_text());accepted=[]
    for row,mode in zip(rows[1:],['dark','light']):
        im=Image.open(root/row['local_image']).convert('RGBA');raw=im.tobytes();assert check(raw,im.size,mode)
        mutants=[]
        for label,index,value in [('last_pixel_alpha',len(raw)-1,0),('wrong_border',0,17),('wrong_interior_channel',(100*320+160)*4+(1 if mode=='dark' else 0),17)]:
            bad=bytearray(raw);bad[index]=value;assert not check(bytes(bad),im.size,mode);mutants.append(label)
        uniform=bytes((255,0,255,255) if mode=='dark' else (0,255,0,255))*64000
        assert not check(uniform,im.size,mode);assert not check(raw[:-4],im.size,mode);assert not check(raw,im.size,'light' if mode=='dark' else 'dark')
        accepted.append({'mode':mode,'pixels_checked':64000,'channels_checked':len(raw),'sha256_rgba':hashlib.sha256(raw).hexdigest(),'all_pixels_match_opaque_primary_subspace':True,'eight_pixel_border_matches_literal_color':True,'nonuniform':True,'negative_controls':mutants+['uniform_without_text','truncated_allocation','swapped_mode']})
    dark=Image.open(root/rows[1]['local_image']).convert('RGBA').tobytes();light=Image.open(root/rows[2]['local_image']).convert('RGBA').tobytes()
    output={'scope':'Native owned sentinel Color literals and opaque black-text color subspace; no independent glyph raster oracle','images':accepted,'different_channels':sum(a!=b for a,b in zip(dark,light)),'padding':'Packed PillowRGBA stride1280; no padding. Native framebuffer padding unobserved.','first_failure':'Actual RichCancelationError/no image retained; no successful initial A or A/A repeatability claim.'}
    (root/'result.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
if __name__=='__main__':main()
