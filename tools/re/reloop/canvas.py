"""Actual Xcode preview capture, controlled variants and owned-process telemetry."""
import json
import pathlib
import re
import shutil
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from reloop.core import ROOT, PROJECT_ROOT, atomic, digest, now
from reloop.ghidra import unpack

FIXTURE = ROOT / 'tools/re/fixtures/PreviewLab'
PROJECT = FIXTURE / 'PreviewLab.xcodeproj'


@contextmanager
def frida_deadline(seconds, factory=None):
    """Cancel synchronous Frida operations; the worker watchdog remains the outer bound."""
    if factory is None:
        import frida
        factory=frida.Cancellable
    cancellation=factory()
    timer=threading.Timer(seconds,cancellation.cancel);timer.daemon=True;timer.start()
    try:
        with cancellation:yield
    finally:timer.cancel()


def workspace(source=FIXTURE, parent=None):
    """Keep Xcode's mutable workspace outside both frozen source and sealed artifacts."""
    parent=pathlib.Path(parent) if parent else PROJECT_ROOT/'research/build/preview-workspaces'
    parent.mkdir(parents=True,exist_ok=True)
    target=parent/('preview-'+uuid.uuid4().hex)
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('xcuserdata','project.xcworkspace','.build','.swiftpm'))
    return target


def compare_captures(images,out):
    if len(images)<2:return {'controlled_change_visible':False,'pixels_identical':False,'preview_bytes_identical':False}
    from reloop.verification import bytes_equal
    from compare_images import compare
    byte_result=bytes_equal(images[0],images[1]);atomic(out/'preview-byte-comparison.json',byte_result)
    difference=compare(images[0],images[1],out/'preview-diff.png');atomic(out/'preview-difference.json',difference)
    return {'controlled_change_visible':bool(difference.get('comparable') and difference['changed_pixels']>0),
            'pixels_identical':bool(difference.get('comparable') and difference['passed']),
            'preview_bytes_identical':byte_result['passed']}


def fixture_content_check(images):
    """Independent sanity prediction for the owned white fixture with two dark text rows.

    Exclude title bar, rounded window corners and borders. This detects blank content;
    positive ink alone does not establish text identity or full rendering conformance.
    """
    from PIL import Image
    checks=[]
    for path in images:
        with Image.open(path) as image:
            if image.size!=(640,384):
                checks.append({'geometry_matches':False,'interior_ink_pixels':None,'passed':False});continue
            pixels=image.convert('RGBA').crop((32,96,608,352)).getdata()
            ink=sum(1 for r,g,b,a in pixels if a>240 and min(r,g,b)<240)
            checks.append({'geometry_matches':True,'interior_ink_pixels':ink,'passed':ink>=100})
    return {'captures':checks,'all_content_nonblank':bool(checks) and all(c['passed'] for c in checks),
            'scope':'Pinned owned white fixture interior sanity, excluding chrome; nonblank is necessary, not OCR or semantic proof.'}


def solid_color_check(images,variants):
    """Exact center-patch predictions from owned explicit sRGB red/blue source literals."""
    from PIL import Image
    expected={2:(255,0,0,255),3:(0,0,255,255)};checks=[]
    for path,index in zip(images,variants):
        if index not in expected:continue
        with Image.open(path) as image:
            width,height=image.size
            box=(width//2-16,height//2-16,width//2+16,height//2+16)
            pixels=list(image.convert('RGBA').crop(box).getdata())
            matched=sum(pixel==expected[index] for pixel in pixels)
            checks.append({'variant':index,'expected_rgba':list(expected[index]),'patch':list(box),
                           'matched_pixels':matched,'compared_pixels':len(pixels),'passed':matched==len(pixels)})
    return {'captures':checks,'all_expected_colors':bool(checks) and all(c['passed'] for c in checks),
            'scope':'Exact 32x32 center patch only, RGBA conversion without resizing/profile conversion; not full-frame equivalence or live wire proof.'}


def select_tab(message, project=PROJECT):
    candidates=[]
    for line in message.splitlines():
        match=re.search(r'tabIdentifier:\s*([^,\s]+),\s*workspacePath:\s*(.+?)\s*$',line)
        if match and pathlib.Path(match[2]).resolve()==pathlib.Path(project).resolve():
            candidates.append(match[1])
    if len(candidates)!=1:raise RuntimeError('Exactly one owned PreviewLab project tab required; close duplicate tabs, not other projects')
    return candidates[0]


def require_closed_owned_workspaces(message,parent=None):
    """Fail before creating/opening another workspace; UI agent closes verified owned windows."""
    parent=pathlib.Path(parent or PROJECT_ROOT/'research/build/preview-workspaces').resolve()
    paths=[pathlib.Path(match).resolve() for match in re.findall(r'workspacePath:\s*(.+?)\s*$',message,re.MULTILINE)]
    if not paths and message.strip()!='No workspace windows found':
        raise RuntimeError('Unrecognized window listing; cannot establish workspace cleanup')
    owned=sorted(set(str(path) for path in paths if parent in path.parents))
    if owned:
        raise RuntimeError('Close prior owned PreviewLab workspace windows before opening another: '+', '.join(owned))
    return {'owned_workspace_windows':0,'scope':'Owned preview-workspaces root only; other user projects untouched.'}


def tools_call(client,name,arguments):
    response=client.request('tools/call',{'name':name,'arguments':arguments})
    if response.get('isError'):raise RuntimeError(str(unpack(response)))
    return unpack(response)


def processes():
    output=subprocess.run(['ps','-axo','pid=,ppid=,lstart=,comm='],capture_output=True,text=True,timeout=5).stdout
    result={}
    for line in output.splitlines():
        fields=line.strip().split(None,7)
        if len(fields)!=8:continue
        command=fields[7]
        if not any(name in command for name in ['PreviewLab','XCPreviewAgent','Xcode Previews']):continue
        result[int(fields[0])]={'pid':int(fields[0]),'ppid':int(fields[1]),'started':' '.join(fields[2:7]),'command':command}
    return result


def owned_mapping(pid, build_root):
    output=subprocess.run(['lsof','-a','-p',str(pid),'-d','txt','-Fn'],capture_output=True,text=True,timeout=5).stdout
    for line in output.splitlines():
        if not line.startswith('n/'):continue
        path=pathlib.Path(line[1:]).resolve()
        if build_root in path.parents and 'PreviewLab' in str(path) and path.is_file():
            return str(path)
    return None


class Monitor:
    def __init__(self,out,build_root,instrument=False):
        self.out=out;self.root=build_root;self.instrument=instrument
        self.events=[];self.sessions={};self.seen=set();self.candidates={};self.stop=threading.Event()
        self.thread=threading.Thread(target=self.observe,daemon=True)

    def start(self):
        self.seen={(pid,info['started'],info['command']) for pid,info in processes().items()};self.thread.start()

    def observe(self):
        device=None
        if self.instrument:
            try:
                import frida
                device=frida.get_local_device()
            except Exception as error:self.events.append({'kind':'instrumentation-unavailable','error':str(error)})
        while not self.stop.wait(.25):
            try:current=processes()
            except Exception as error:
                self.events.append({'kind':'monitor-error','error':str(error)});continue
            for pid,info in current.items():
                identity=(pid,info['started'],info['command'])
                if identity in self.seen:continue
                if identity not in self.candidates:
                    event={**info,'kind':'process-observed','host_monotonic_ns':time.monotonic_ns(),'timestamp':now(),
                           'ownership':'candidate; launch timing alone is insufficient'}
                    self.events.append(event);self.candidates[identity]=event
                event=self.candidates[identity]
                try:mapped=owned_mapping(pid,self.root)
                except Exception as error:
                    event['mapping_error']=str(error);mapped=None
                if not mapped:continue
                if processes().get(pid)!=info:continue
                self.seen.add(identity)
                event.update(ownership='verified fixture build-root mapping',mapped_image=mapped,image_sha256=digest(mapped))
                if device:
                    try:
                        def message(value,data,process_id=pid):
                            record={'kind':'frida-message','pid':process_id,'host_monotonic_ns':time.monotonic_ns(),'message':value}
                            if data is not None:
                                import base64
                                record['base64']=base64.b64encode(data).decode()
                            self.events.append(record)
                        self.events.append({'kind':'attach-started','pid':pid,'deadline_seconds':10})
                        with frida_deadline(10):
                            session=device.attach(pid)
                            self.sessions[pid]=(session,None)
                            self.events.append({'kind':'session-created','pid':pid})
                            script=session.create_script((pathlib.Path(__file__).parent/'preview_hooks.js').read_text())
                            self.sessions[pid]=(session,script)
                            self.events.append({'kind':'script-load-started','pid':pid})
                            script.on('message',message);script.load()
                        self.events.append({'kind':'attached','pid':pid,'coverage':'late attach; earlier events may be missing'})
                    except Exception as error:self.events.append({'kind':'attach-failed','pid':pid,'error':str(error)})

    def close(self):
        self.stop.set();self.thread.join(timeout=12)
        for session,script in self.sessions.values():
            for operation in ([script.unload] if script is not None else [])+[session.detach]:
                try:
                    with frida_deadline(3):operation()
                except Exception as error:self.events.append({'kind':'cleanup-error','error':str(error)})
        atomic(self.out/'preview-lifecycle.json',{'events':self.events,
            'scope':'Owned mapping required before instrumentation; no protected-process bypass. Candidate processes are not asserted owned.',
            'wire_capture_complete':False,
            'cleanup_completed':not self.thread.is_alive() and not any(e.get('kind')=='cleanup-error' for e in self.events),
            'cleanup':'Instrumentation cleanup attempted; inspect phase/error events. Xcode owns preview process lifecycle; user sessions were not terminated.'})
        if self.thread.is_alive():raise RuntimeError('Instrumentation attach did not return; partial evidence saved; outer watchdog must reconcile process')


def capture(out,variants=(0,1),trace=False):
    out=pathlib.Path(out)
    from reloop.xcodebridge import BrokerClient
    preflight=BrokerClient()
    try:
        windows=tools_call(preflight,'XcodeListWindows',{})
        atomic(out/'window-preflight.json',windows)
        require_closed_owned_workspaces(windows['message'])
    finally:preflight.close()
    # Xcode rewrites scheme/workspace metadata. Keep executable source snapshots untouched.
    fixture=workspace()
    project=fixture/'PreviewLab.xcodeproj'
    source_hash=digest(fixture/'Sources/PreviewLab/PreviewLab.swift')
    atomic(out/'workspace-lifecycle.json',{'project':str(project),'cleanup_required':True,
          'instruction':'UI agent must close this owned workspace when finished, including failure, and verify no owned workspace windows before another capture.'})
    subprocess.run(['open','-a','Xcode',str(project)],check=True,timeout=15)
    settings=subprocess.run(['xcodebuild','-project',str(project),'-scheme','PreviewLab','-configuration','Debug','-sdk','macosx','-destination','platform=macOS,arch=arm64','-destination-timeout','5','-showBuildSettings','-json'],capture_output=True,text=True,timeout=90)
    (out/'build-settings.stderr').write_text(settings.stderr)
    if settings.returncode:raise RuntimeError('Fixture build settings unavailable')
    values=json.loads(settings.stdout)[0]['buildSettings'];atomic(out/'build-settings.json',values)
    if pathlib.Path(values['PROJECT_FILE_PATH']).resolve()!=project.resolve():raise RuntimeError('Build settings project mismatch')
    build_root=pathlib.Path(values['BUILD_DIR']).resolve().parent
    # Establish target membership and a compiled reference before preview instrumentation.
    with (out/'fixture-build.log').open('wb') as log:
        built=subprocess.run(['xcodebuild','-project',str(project),'-scheme','PreviewLab','-configuration','Debug',
                              '-sdk','macosx','-destination','platform=macOS,arch=arm64','-destination-timeout','5','build'],
                             stdout=log,stderr=subprocess.STDOUT,timeout=180)
    if built.returncode:raise RuntimeError('Owned native fixture build failed; inspect fixture-build.log')
    monitor=Monitor(out,build_root,trace);client=None;images=[]
    with (out/'xcode-bridge.stderr').open('wb') as stderr:
        try:
            client=BrokerClient()
            atomic(out/'broker-identity.json',client.metadata)
            schema=client.request('tools/list',{});atomic(out/'xcode-schema.json',schema)
            names={t['name'] for t in schema['tools']}
            if not {'RenderPreview','XcodeListWindows','XcodeGlob','XcodeRead'}<=names:raise RuntimeError('Installed Xcode lacks required preview tools')
            windows=tools_call(client,'XcodeListWindows',{});atomic(out/'windows.json',windows)
            tab=select_tab(windows['message'],project)
            files=tools_call(client,'XcodeGlob',{'tabIdentifier':tab,'pattern':'**/*.swift'})
            atomic(out/'project-files.json',files)
            matches=sorted(set(p for p in files['matches'] if p.endswith('PreviewLab.swift')))
            if len(matches)!=1:raise RuntimeError('Owned preview source path ambiguous')
            atomic(out/'project-source.json',tools_call(client,'XcodeRead',{'tabIdentifier':tab,'filePath':matches[0]}))
            monitor.start()
            for ordinal,index in enumerate(variants):
                result=tools_call(client,'RenderPreview',{'tabIdentifier':tab,'sourceFilePath':matches[0],
                                 'previewDefinitionIndexInFile':index,'timeout':60})
                atomic(out/('preview-%d-definition-%d-response.json'%(ordinal,index)),result)
                if result.get('errors') or not result.get('previewSnapshotPath'):
                    raise RuntimeError('Xcode preview failed; inspect response artifact')
                source=pathlib.Path(result['previewSnapshotPath']).resolve(strict=True)
                if source.stat().st_size>64*1024*1024:raise RuntimeError('Preview snapshot exceeds limit')
                from PIL import Image
                with Image.open(source) as image:
                    if image.format!='PNG' or image.width*image.height>16*1024*1024:raise RuntimeError('Unexpected preview image')
                    image.verify()
                dest=out/('preview-%d-definition-%d.png'%(ordinal,index));shutil.copyfile(source,dest);images.append(dest)
        finally:
            if client:client.close()
            if monitor.thread.ident is not None:monitor.close()
    comparison=compare_captures(images,out)
    content=fixture_content_check(images);atomic(out/'fixture-content-check.json',content)
    solid=solid_color_check(images,variants);atomic(out/'solid-color-check.json',solid)
    if len(images)==3 and tuple(variants)==(0,0,1):
        changed_dir=out/'controlled-change';changed_dir.mkdir()
        changed=compare_captures(images[1:],changed_dir)
        comparison['controlled_change_visible']=changed['controlled_change_visible']
        comparison['changed_preview_bytes_identical']=changed['preview_bytes_identical']
    if digest(fixture/'Sources/PreviewLab/PreviewLab.swift')!=source_hash:raise RuntimeError('Fixture source changed during reference capture')
    return {'rendered_variants':len(images),'png_valid':True,
            'fixture_content_nonblank':content['all_content_nonblank'],
            'fixture_nonblank_captures':sum(c['passed'] for c in content['captures']),
            'solid_expected_colors':solid['all_expected_colors'],
            **comparison,
            'observed_processes':sum(e.get('kind')=='process-observed' for e in monitor.events),
            'instrumented_processes':sum(e.get('kind')=='attached' for e in monitor.events),
            'sessions_created':len(monitor.sessions),'wire_capture_complete':False,
            'source_sha256':source_hash}
