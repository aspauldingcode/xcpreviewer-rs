import base64
import json
import os
import pathlib
import plistlib
import subprocess
import sys
import time
from reloop.core import ROOT, PROJECT_ROOT, atomic, digest, load


def run(argv,out,name):
    with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
        r=subprocess.run([str(a) for a in argv],stdout=stdout,stderr=stderr,timeout=120)
    if r.returncode:raise RuntimeError(name+' failed; inspect stderr')


def build_target(out):
    target=out/'owned-trace-target'
    run(['xcrun','clang','-g','-O0','-fobjc-arc','-framework','Foundation','-Wl,-export_dynamic',
         ROOT/'tools/re/fixtures/trace_target.m','-o',target],out,'compile')
    run(['codesign','--force','--sign','-','--entitlements',ROOT/'tools/re/fixtures/debug.entitlements',target],out,'sign')
    return target


def smoke(kind,out):
    if kind=='native_reference':
        target=out/'reference-capture'
        run(['xcrun','swiftc','-parse-as-library','-module-cache-path',out/'swift-cache',ROOT/'tools/re/fixtures/Reference.swift','-o',target],out,'compile')
        run([target,out/'reference.png'],out,'capture')
        image=(out/'reference.png').read_bytes()
        return {'png_valid':image.startswith(b'\x89PNG\r\n\x1a\n'),'image_sha256':digest(out/'reference.png'),
                'kind':'owned SwiftUI ImageRenderer reference, not Xcode canvas capture'}
    target=build_target(out)
    if kind=='lldb_smoke':
        # LLDB command quoting, not shell evaluation. Paths originate in our run.
        import shlex
        run(['xcrun','lldb','--batch',str(target),'-o','command script import '+shlex.quote(str(ROOT/'tools/re/reloop/lldb_capture.py')),
             '-o','re-capture '+str(out),'-o','quit'],out,'lldb')
        data=load(out/'capture.json')
        if data is None:raise RuntimeError('LLDB did not produce a capture')
        return {'completed':data['completed'],'tick_events':len(data['events']),
                'inputs_match':[e['input'] for e in data['events']]==list(range(6)),
                'breakpoint_resolved':data['breakpoint_locations']>0,'target_sha256':digest(target)}
    os.environ.setdefault("XDG_CACHE_HOME",str(PROJECT_ROOT/"research/build/cache"))
    import frida
    device=frida.get_local_device();pid=None;session=None;process=None
    events=[];errors=[]
    try:
        marker=out/'resume.marker'
        with (out/'target.stdout').open('wb') as stdout,(out/'target.stderr').open('wb') as stderr:
            process=subprocess.Popen([str(target),str(marker)]+(['preload'] if kind=='preview_hook_smoke' else []),stdout=stdout,stderr=stderr)
        pid=process.pid
        from reloop.canvas import frida_deadline
        with frida_deadline(10):
            session=device.attach(pid)
            script=session.create_script((ROOT/('tools/re/reloop/preview_hooks.js' if kind=='preview_hook_smoke' else 'tools/re/reloop/frida_hooks.js')).read_text())
        def message(m,data):
            if m['type']=='send':
                event=m['payload']
                if data is not None:event['base64']=base64.b64encode(data).decode()
                events.append(event)
            elif m['type']=='error':errors.append(m)
        script.on('message',message)
        with frida_deadline(10):script.load()
        if kind=='preview_hook_smoke':
            ready=time.monotonic()+5
            while time.monotonic()<ready and not any(e.get('kind')=='hook-installed' for e in events):time.sleep(.02)
            if not any(e.get('kind')=='hook-installed' for e in events):raise RuntimeError('Preview data hook did not become ready before owned target resume')
        marker.touch()
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and len([e for e in events if e.get('kind')=='plist-data'])<6:
            time.sleep(.05)
        atomic(out/'frida-events.json',events);atomic(out/'frida-errors.json',errors)
        payloads=[plistlib.loads(base64.b64decode(e['base64'])) for e in events if e.get('kind')=='plist-data']
        ticks=[e for e in events if e.get('kind')=='tick']
        if kind=='preview_hook_smoke':
            return {'frida_version':frida.__version__,'plist_events':len(payloads),
                    'payloads_match':[p['value'] for p in payloads]==list(range(1,7)) and all(p['type']=='owned-trace-probe' for p in payloads),
                    'hook_installed':any(e.get('kind')=='hook-installed' for e in events),
                    'script_errors':len(errors)+sum(e.get('kind')=='capture-error' for e in events),
                    'target_sha256':digest(target),'scope':'Canvas hook validated on owned synthetic helper; native preview attach remains unverified.'}
        return {'frida_version':frida.__version__,'tick_events':len(ticks),'plist_events':len(payloads),
                'inputs_match':[e['input'] for e in ticks]==list(range(6)),
                'payloads_match':[p['value'] for p in payloads]==list(range(1,7)) and all(p['type']=='owned-trace-probe' for p in payloads),
                'script_errors':len(errors)+sum(e.get('kind')=='capture-error' for e in events),'target_sha256':digest(target),
                'scope':'owned synthetic helper, not a captured Xcode preview session'}
    finally:
        atomic(out/'frida-events.json',events);atomic(out/'frida-errors.json',errors)
        if session:
            try:
                with frida_deadline(3):session.detach()
            except Exception as error:
                errors.append({'phase':'cleanup','error':str(error)})
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        atomic(out/'frida-errors.json',errors)
