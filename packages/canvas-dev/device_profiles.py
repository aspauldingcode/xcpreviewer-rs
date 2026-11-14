"""Read installed device geometry; Apple mask assets stay local and are never vendored."""
from pathlib import Path
import hashlib,json,math,plistlib,re

DEVICE_ROOT=Path('/Library/Developer/CoreSimulator/Profiles/DeviceTypes')

def sha(data):return hashlib.sha256(data).hexdigest()

def load_profiles(root=DEVICE_ROOT):
    profiles={'desktop':dict(id='desktop',name='Desktop window',family='desktop',point_width=600,point_height=400,evidence='Resizable preview window; decorative AppKit-style frame')};assets={}
    if not root.is_dir():return profiles,assets
    for package in sorted(root.glob('*.simdevicetype')):
        if not package.stem.startswith(('iPhone','iPad','Apple Watch')):continue
        try:
            resources=package/'Contents/Resources';cap_bytes=(resources/'capabilities.plist').read_bytes();profile_bytes=(resources/'profile.plist').read_bytes()
            if len(cap_bytes)>1024*1024 or len(profile_bytes)>1024*1024:continue
            caps=plistlib.loads(cap_bytes)['capabilities'];profile=plistlib.loads(profile_bytes)
            for display in caps.get('displays',[]):
                display_name=display.get('deviceName','')
                if not display_name.startswith('primary'):continue
                scale=display.get('scale',0);width=display.get('canvasWidth',display.get('width',0));height=display.get('canvasHeight',display.get('height',0))
                if not all(isinstance(v,(float,int)) and math.isfinite(v) and v>0 for v in [width,height,scale]):continue
                pw,ph=width/scale,height/scale
                if pw!=int(pw) or ph!=int(ph) or not(64<=pw<=2048 and 64<=ph<=2048):continue
                identifier=package.stem+':'+display_name
                mask=display.get('framebufferMaskIdentifier') or (profile.get('framebufferMask') if display_name=='primary' else None)
                path=resources/(mask+'.pdf') if isinstance(mask,str) and re.fullmatch(r'[A-Za-z0-9_-]+',mask) else None
                mask_bytes=path.read_bytes() if path and path.is_file() else None
                if mask_bytes and len(mask_bytes)>1024*1024:continue
                family='iphone' if package.stem.startswith('iPhone') else 'ipad' if package.stem.startswith('iPad') else 'watch'
                profiles[identifier]=dict(id=identifier,name=package.stem+(' · '+display_name if display_name!='primary' else ''),family=family,
                    point_width=int(pw),point_height=int(ph),native_scale=scale,framebuffer_width=display['width'],framebuffer_height=display['height'],
                    layout_pixel_width=width,layout_pixel_height=height,screen_aspect_ratio=[int(width),int(height)],
                    corner_radii_points=[display.get(k) for k in ['cornerRadiusUL','cornerRadiusUR','cornerRadiusLR','cornerRadiusLL']],
                    mask_sha256=sha(mask_bytes) if mask_bytes else None,catalog_sha256=sha(cap_bytes+profile_bytes),
                    evidence='Installed Xcode device catalog geometry; Mac SwiftUI renderer, iOS behavior not verified',
                    frame_scope='Exact installed screen mask' if mask_bytes else 'Rectangular display; hardware bezel not qualified')
                if mask_bytes:assets[identifier]=path
        except (OSError,ValueError,TypeError,KeyError,plistlib.InvalidFileException):continue
    return profiles,assets

if __name__=='__main__':
    import argparse,os,subprocess,sys,platform
    p=argparse.ArgumentParser();p.add_argument('--render',required=True);p.add_argument('--scale',type=int,choices=[1,2],required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    profiles,assets=load_profiles();profile=profiles[a.render];mask=assets[a.render]
    # Reuse the original bounded, owned-process runner: cancellation reaps its group.
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/re/swiftui-preview'))
    from capture import run
    environment={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
    a.work.mkdir(parents=True,exist_ok=True);source=Path(__file__).with_name('RenderPDF.swift')
    sdk_version=run(['xcrun','--show-sdk-version'],10,environment).decode().strip()
    if int(sdk_version.split('.')[0])<27:raise ValueError('Device mask rendering requires Apple SDK 27 or newer')
    version=run(['xcrun','swiftc','--version'],10,environment);key=sha(source.read_bytes()+version+b'macos27.0')[:20]
    executable=a.work/('render-pdf-'+key)
    if not executable.is_file():run(['xcrun','swiftc','-swift-version','6','-target',platform.machine()+'-apple-macos27.0','-parse-as-library',str(source),'-o',str(executable)],30,environment)
    width=profile['point_width']*a.scale;height=profile['point_height']*a.scale
    output=a.work/(profile['mask_sha256']+'-'+str(a.scale)+'.png')
    receipt=json.loads(run([str(executable),str(mask),str(width),str(height),str(output)],8,environment))
    if [receipt['pdf_width'],receipt['pdf_height']]!=[profile['layout_pixel_width'],profile['layout_pixel_height']]:raise ValueError('Installed mask size differs from declared layout canvas; profile requires qualification')
    print(json.dumps(dict(output=str(output),sha256=sha(output.read_bytes()),**receipt)))
