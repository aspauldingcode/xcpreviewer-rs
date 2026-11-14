#!/usr/bin/env python3
"""Local source-bound Canvas development server, with bounded original build backends."""
from pathlib import Path
import argparse, hashlib, http.server, json, os, secrets, shutil, signal, subprocess
import sys, tempfile, threading, time, urllib.parse, platform, plistlib, math
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent
sys.path.insert(0, str(ASSETS))
from project import resolve_source, preview_snapshot, select_factory, strip_preview_blocks
from device_profiles import load_profiles
from live_host import NativeHost
MAX_SOURCE = 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


@contextmanager
def native_controller():
    import fcntl
    path=ROOT/'research/state/controller.lock';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Native controller busy; retry after the active native operation finishes')
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)


class Session:
    def __init__(self, source, work, *, factory=None, interactive=False, width=600, height=400, extra_sources=None, project=None, title=None,
                 clang=None, wasm_ld=None, node=None, debounce=.2):
        self.source = Path(source).resolve(strict=True)
        self.work = Path(work).resolve(); self.work.mkdir(parents=True, exist_ok=True)
        self.factory, self.width, self.height = factory, width, height
        if interactive and not factory:raise ValueError('Interactive input requires a native SwiftUI factory')
        self.interactive=interactive;self.host=None;self.pending_host=None
        self.extra_sources = extra_sources or []; self.project = project
        self.title = title or self.source.stem
        self.devices,self.device_masks=load_profiles();self.pending_assets={}
        self.config = dict(appearance='auto', color_scheme='light', scale=2,
                           chrome=bool(factory), width=width, height=height, device='desktop')
        self.active_settings = dict(self.config); self.active_extras=[]
        self.active_project = dict(project) if project else None
        self.tools = dict(clang=clang, wasm_ld=wasm_ld, node=node)
        self.debounce = debounce
        self.lock = threading.RLock(); self.stopped = threading.Event()
        self.thread = None; self.child = None; self.force = 0; self.observed = None
        self.state = dict(state='starting', generation=0, revision=0, error=None,
                          frame=None, build_ms=None, source_name=self.source.name,
                          backend='swiftui' if factory else 'portable', interactive=interactive)
        self.blobs = {}

    def read_source(self):
        with self.source.open('rb') as stream:
            data = stream.read(MAX_SOURCE + 1)
        if len(data) > MAX_SOURCE:
            raise ValueError('Source exceeds 1 MiB')
        return data.decode('utf-8'), sha(data)

    def snapshot(self):
        with self.lock:
            value = dict(self.state)
            value['config'] = dict(self.config)
            value['devices'] = list(self.devices.values())
            value['protocol_version'] = 1
            value['project'] = {k:self.project[k] for k in ['name','target','scope']} if self.project else None
            try:
                text, digest = self.read_source()
                value.update(source=text, source_sha256=digest)
            except (OSError, UnicodeError, ValueError) as error:
                value.update(source=None, source_sha256=None, source_error=str(error))
            return value

    def read_inputs(self):
        text, digest = self.read_source(); pieces=[text.encode('utf-8')]; extras=[]; total=len(pieces[0])
        project=self.project
        if project:
            manifest=Path(project['manifest'])
            with manifest.open('rb') as stream:manifest_bytes=stream.read(MAX_SOURCE+1)
            if len(manifest_bytes)>MAX_SOURCE:raise ValueError('Project manifest exceeds 1 MiB')
            primary,extra_sources,project=resolve_source(manifest.parent,self.factory,project['target'])
            if primary!=self.source:raise ValueError('Preview factory moved; restart to bind its new source file')
            with manifest.open('rb') as stream:current_manifest=stream.read(MAX_SOURCE+1)
            if current_manifest!=manifest_bytes:raise ValueError('Project changed during source discovery; waiting for a stable revision')
            with self.lock:
                self.extra_sources=extra_sources;self.project=project
        else:extra_sources=self.extra_sources
        for path in extra_sources:
            with path.open('rb') as stream:data=stream.read(MAX_SOURCE+1)
            total += len(data)
            if len(data)>MAX_SOURCE or total>8*MAX_SOURCE:raise ValueError('Project source bounds exceeded')
            data.decode('utf-8');extras.append((path,data));pieces.extend([str(path).encode(),data])
        if project:pieces.append(manifest_bytes)
        combined=sha(b''.join(len(part).to_bytes(8,'big')+part for part in pieces))
        return text,digest,combined,extras

    def configure(self, value):
        with self.lock:
            current=dict(self.config);current.update({k:v for k,v in value.items() if k in current})
            if current['device'] not in self.devices:raise ValueError('Choose an installed device profile')
            if current['device']!='desktop' and not self.factory:raise ValueError('Device profiles require the native SwiftUI backend')
            if current['device']!='desktop':
                profile=self.devices[current['device']];current.update(width=profile['point_width'],height=profile['point_height'],chrome=False)
            elif current['device']!=self.config['device']:
                current.update(width=self.width,height=self.height,chrome=True)
            if current['appearance'] not in ['auto','light','dark'] or current['color_scheme'] not in ['light','dark']:
                raise ValueError('Choose Auto, Light or Dark')
            if type(current['scale']) is not int or current['scale'] not in [1,2] or type(current['chrome']) is not bool:
                raise ValueError('Choose 1x or 2x rendering and a window-frame toggle')
            if any(type(current[k]) is not int or not 64<=current[k]<=2048 for k in ['width','height']):
                raise ValueError('Preview window dimensions must be 64–2048 points')
            body_height=current['height']-(32 if current['chrome'] else 0)
            if current['width']*body_height*current['scale']**2*4>32*1024*1024:raise ValueError('Preview exceeds 32 MiB')
            if current!=self.config:self.config=current;self.force+=1
            return dict(self.config)

    def save(self, text, expected):
        if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_SOURCE:
            raise ValueError('Source must be UTF-8 text of at most 1 MiB')
        with self.lock:
            _, current = self.read_source()
            if current != expected:
                raise FileExistsError('Source changed on disk; reload it before saving your edits')
            # Write only the explicitly selected file. Preserve permissions and detect
            # external edits again immediately before the atomic replacement.
            mode = self.source.stat().st_mode & 0o777
            fd, name = tempfile.mkstemp(prefix='.canvas-save-', dir=self.source.parent)
            temporary = Path(name)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(text.encode('utf-8')); stream.flush(); os.fsync(stream.fileno())
                os.chmod(temporary, mode)
                if self.read_source()[1] != expected:
                    raise FileExistsError('Source changed during save; edits were not written')
                os.replace(temporary, self.source)
            finally:
                temporary.unlink(missing_ok=True)
            return sha(text.encode('utf-8'))

    def refresh(self):
        with self.lock:
            self.force += 1

    def start(self):
        self.thread = threading.Thread(target=self.watch, name='canvas-build', daemon=True)
        self.thread.start()

    def close(self):
        self.stopped.set()
        with self.lock:
            child = self.child
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
        if self.thread:
            self.thread.join(timeout=5)
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=3)
        for host in [self.host,self.pending_host]:
            if host:host.close()

    def command(self, args, *, json_output=True, timeout=100):
        with self.lock:
            if self.stopped.is_set():
                raise RuntimeError('Preview server stopped')
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            self.child = process
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)
            try:
                stdout, stderr = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.communicate()
            raise RuntimeError('Preview build exceeded its deadline') from None
        finally:
            with self.lock:
                self.child = None
        if self.stopped.is_set():
            raise RuntimeError('Preview server stopped')
        if process.returncode:
            try:
                message = json.loads(stdout).get('error')
            except (ValueError, AttributeError):
                message = None
            raise RuntimeError(message or stderr.decode(errors='replace')[-12000:] or 'Build failed')
        return json.loads(stdout) if json_output else stdout

    def build(self, text, digest):
        self.pending_assets={}
        with tempfile.TemporaryDirectory(prefix='attempt-', dir=self.work) as name:
            attempt = Path(name); source = attempt/'Source.swift'
            settings=self.active_settings;compiled,removed=preview_snapshot(text) if self.factory else (text,0)
            preview_blocks_removed=0
            if self.factory:compiled,preview_blocks_removed=strip_preview_blocks(compiled)
            source.write_text(compiled)
            extra_paths=[]
            for index,(_,data) in enumerate(self.active_extras):
                extra,_=preview_snapshot(data.decode('utf-8'))
                if self.factory:extra,_=strip_preview_blocks(extra)
                path=attempt/('Local'+str(index)+'.swift');path.write_text(extra);extra_paths.append(path)
            if self.factory:
                factory=select_factory(text,self.factory)
                output = attempt/'capture.bplist'
                body_height=settings['height']-(32 if settings['chrome'] else 0)
                command=[sys.executable, str(ROOT/'tools/re/swiftui-preview/capture.py'),str(source),
                         '--factory',factory,'--width',str(settings['width']),'--height',str(body_height),
                         '--scale',str(settings['scale']),'--color-scheme',settings['color_scheme'],
                         '--minimum-macos','27.0','--module-cache',str(self.work/'module-cache'),'--output',str(output)]
                for path in extra_paths:command+=['--extra-source',str(path)]
                if self.active_project:
                    command+=['--swift-version',self.active_project['swift_version']]
                    if self.active_project.get('default_isolation') in ['MainActor','nonisolated']:
                        command+=['--default-isolation',self.active_project['default_isolation']]
                with native_controller():
                    if self.interactive:
                        wrapper=(ASSETS/'LiveHost.swift.template').read_text().replace('__PREVIEW_CONTENT__','('+factory+'()).environment(\\.colorScheme, .'+settings['color_scheme']+')').replace('__APPEARANCE__','.darkAqua' if settings['color_scheme']=='dark' else '.aqua')
                        wrapper_path=attempt/'LiveHost.swift';wrapper_path.write_text(wrapper)
                        executable=attempt/'live-host'
                        compiler=self.command(['xcrun','--find','swiftc'],json_output=False,timeout=10).decode().strip()
                        version=self.command([compiler,'--version'],json_output=False,timeout=10).decode().strip()
                        sdk=self.command(['xcrun','--show-sdk-path'],json_output=False,timeout=10).decode().strip()
                        sdk_version=self.command(['xcrun','--show-sdk-version'],json_output=False,timeout=10).decode().strip()
                        if int(sdk_version.split('.')[0])<27:raise ValueError('Native preview requires an Apple SDK 27 or newer')
                        args=[compiler,'-parse-as-library','-sdk',sdk,'-target',platform.machine()+'-apple-macos27.0','-swift-version',self.active_project['swift_version'] if self.active_project else '6']
                        if self.active_project and self.active_project.get('default_isolation') in ['MainActor','nonisolated']:args+=['-default-isolation',self.active_project['default_isolation']]
                        host_work=Path(tempfile.mkdtemp(prefix='live-',dir=self.work))
                        try:
                            self.command(args+[str(source),*[str(p) for p in extra_paths],str(wrapper_path),'-o',str(executable)],json_output=False,timeout=30)
                            self.pending_host=NativeHost(executable,host_work,settings['width'],body_height,settings['scale'])
                            live_receipt,live_data=self.pending_host.request('capture');output.write_bytes(live_data)
                        except Exception:
                            if self.pending_host:self.pending_host.close();self.pending_host=None
                            shutil.rmtree(host_work,ignore_errors=True);raise
                        receipt=dict(payload_sha256=sha(live_data),producer='AppKit.NSHostingView',compiler_version=version,sdk_version=sdk_version,source_sha256=sha(source.read_bytes()))
                    else:receipt = self.command(command)
                    mask_receipt=None
                    if settings['device'] in self.device_masks:
                        mask_receipt=self.command([sys.executable,str(ASSETS/'device_profiles.py'),'--render',settings['device'],'--scale',str(settings['scale']),'--work',str(self.work/'device-masks')])
                        mask_bytes=Path(mask_receipt['output']).read_bytes()
                        if sha(mask_bytes)!=mask_receipt['sha256']:raise ValueError('Mask integrity mismatch')
                        self.pending_assets[mask_receipt['sha256']]=mask_bytes
                data = output.read_bytes()
                if sha(data) != receipt['payload_sha256']:
                    raise ValueError('Capture hash mismatch')
                frame = dict(kind='swiftui', width=settings['width'], height=body_height,
                             source_sha256=digest, sha256=sha(data),
                             producer=receipt['producer'], compiler_version=receipt['compiler_version'], deployment_target=receipt.get('deployment_target',platform.machine()+'-apple-macos27.0'),sdk_version=receipt.get('sdk_version'),factory=factory,
                             compiled_source_sha256=receipt['source_sha256'], app_entry_attributes_removed=removed, preview_blocks_removed=preview_blocks_removed)
            else:
                if not text.isascii() or len(text) > 4096:
                    raise ValueError('Portable mode currently accepts one primary-layer expression (4 KiB ASCII)')
                args = [sys.executable, str(ROOT/'tools/re/preview_cli.py'), str(source),
                        '--cache', str(self.work/'cache'), '--output', str(self.work/'frames')]
                for key, value in self.tools.items():
                    if not value:
                        raise ValueError('Missing '+key.replace('_', '-')+'; install LLVM with WebAssembly support and Node.js')
                    args += ['--'+key.replace('_', '-'), str(value)]
                receipt = self.command(args)
                bundle = self.work/'frames/versions'/receipt['entry_sha256']
                data = (bundle/'view.wasm').read_bytes()
                if sha(data) != receipt['module_sha256']:
                    raise ValueError('Renderer hash mismatch')
                frame = dict(kind='portable', width=receipt['config']['width'],
                             height=receipt['config']['height'], stride=receipt['stride'],
                             source_sha256=digest, sha256=sha(data),
                             allocation_sha256=receipt['allocation_sha256'])
            if len(data) > 64*1024*1024:
                raise ValueError('Preview artifact exceeds 64 MiB')
            if self.interactive and self.pending_host:frame.update(input_mode='appkit-mouse',live_host_id=self.pending_host.identity,native_backing_width=live_receipt['native_backing_width'],native_backing_height=live_receipt['native_backing_height'])
            frame['device_profile']=self.devices[settings['device']]
            if self.factory and mask_receipt:frame['screen_mask_sha256']=mask_receipt['sha256']
            frame.update(scale=settings['scale'], color_scheme=settings['color_scheme'],
                         chrome=settings['chrome'], title=self.title)
            return frame, data

    def input(self, value):
        x,y=value.get('x'),value.get('y')
        if any(type(v) not in [int,float] or not math.isfinite(v) for v in [x,y]):raise ValueError('Input coordinates must be finite points')
        with self.lock:
            host=self.host;frame=dict(self.state['frame'] or {})
            if not host or frame.get('live_host_id')!=value.get('live_host_id'):raise FileExistsError('Native view changed; wait for the current preview')
            if not(0<=x<host.width and 0<=y<host.height):raise ValueError('Input lies outside the preview content')
            mask_data=self.blobs.get(frame.get('screen_mask_sha256'))
        if mask_data:
            import io
            from PIL import Image
            with Image.open(io.BytesIO(mask_data)) as image:
                if image.convert('RGBA').getpixel((int(x*host.scale),int(y*host.scale)))[3]==0:raise ValueError('Input lies outside the visible device mask')
        with native_controller():receipt,data=host.request('click',x=x,y=y)
        bitmap=plistlib.loads(data)['bitmapDescription']
        if bitmap['width']!=host.width*host.scale or bitmap['height']!=host.height*host.scale or len(bitmap['data'])!=host.width*host.height*host.scale**2*4:raise ValueError('Native input returned invalid extent')
        with self.lock:
            if self.host is not host:raise FileExistsError('Native view changed during input; result discarded')
            frame.update(sha256=sha(data),input_event_sequence=receipt['event_sequence'])
            mask=frame.get('screen_mask_sha256')
            if mask in self.blobs:blob=self.blobs.pop(mask);self.blobs[mask]=blob
            self.blobs.pop(frame['sha256'],None);self.blobs[frame['sha256']]=data
            while len(self.blobs)>8:del self.blobs[next(iter(self.blobs))]
            self.state.update(frame=frame,revision=self.state['revision']+1)
        return dict(ok=True,events=receipt['events'],event_sequence=receipt['event_sequence'])

    def watch(self):
        while not self.stopped.is_set():
            try:
                text, digest, inputs, extras = self.read_inputs()
                with self.lock:
                    key = (inputs, self.force)
                if key == self.observed:
                    self.stopped.wait(.15); continue
                if self.stopped.wait(self.debounce):
                    break
                if self.read_inputs()[2] != inputs:
                    continue
                self.observed = key
                with self.lock:
                    self.active_settings=dict(self.config);self.active_extras=extras
                    self.active_project=dict(self.project) if self.project else None
                    self.state.update(state='building', error=None,
                                      generation=self.state['generation']+1)
                started = time.monotonic()
                try:
                    frame, data = self.build(text, digest)
                    # Results from a source version superseded while building cannot publish.
                    if self.read_inputs()[2] != inputs or key[1] != self.force:
                        continue
                    with self.lock:
                        for digest,blob in {**self.pending_assets,frame['sha256']:data}.items():
                            self.blobs.pop(digest,None);self.blobs[digest]=blob
                        old_host=self.host
                        if self.pending_host:self.host=self.pending_host;self.pending_host=None
                        # Keep a small number of immutable revisions for in-flight readers.
                        while len(self.blobs) > 8:
                            del self.blobs[next(iter(self.blobs))]
                        self.state.update(state='ready', error=None, frame=frame,
                                          revision=self.state['revision']+1,
                                          build_ms=round((time.monotonic()-started)*1000))
                    if old_host and old_host is not self.host:old_host.close()
                except Exception as error:
                    if self.stopped.is_set():
                        break
                    try:
                        if self.read_inputs()[2] != inputs:
                            continue
                    except (OSError, UnicodeError, ValueError):
                        pass
                    with self.lock:
                        self.state.update(state='error', error=str(error)[-12000:])
                finally:
                    if self.pending_host:self.pending_host.close();self.pending_host=None
            except (OSError, UnicodeError, ValueError) as error:
                self.observed = None
                with self.lock:
                    self.state.update(state='error', error=str(error)[-12000:])
                self.stopped.wait(.25)


class Handler(http.server.BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json'):
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime); self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' blob:")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def valid_host(self):
        return self.headers.get('Host') == self.server.authority

    def do_GET(self):
        if not self.valid_host():
            self.reply(403, {'error':'Local host mismatch'}); return
        path = urllib.parse.urlsplit(self.path).path
        if path == '/api/session':
            self.reply(200, {**self.server.session.snapshot(), 'token':self.server.token}); return
        if path.startswith('/artifact/'):
            digest = path.removeprefix('/artifact/')
            with self.server.session.lock:
                data = self.server.session.blobs.get(digest)
            if data is None:
                self.reply(404, {'error':'Preview revision unavailable'}); return
            self.reply(200, data, 'application/wasm' if data[:4] == b'\0asm' else 'application/octet-stream'); return
        route = self.server.assets.get(path)
        if route:
            self.reply(200, route[0].read_bytes(), route[1]); return
        self.reply(404, {'error':'Not found'})

    def do_POST(self):
        if (not self.valid_host() or self.headers.get('Origin') != 'http://'+self.server.authority
                or self.headers.get('X-Canvas-Token') != self.server.token
                or self.headers.get('Content-Type') != 'application/json'):
            self.reply(403, {'error':'Local session authorization required'}); return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2*MAX_SOURCE:
                raise ValueError('Invalid request length')
            value = json.loads(self.rfile.read(length))
            if self.path == '/api/source':
                digest = self.server.session.save(value['source'], value['expected_sha256'])
                self.reply(200, {'source_sha256':digest})
            elif self.path == '/api/environment':
                self.reply(200, self.server.session.configure(value))
            elif self.path == '/api/input':
                self.reply(200,self.server.session.input(value))
            elif self.path == '/api/refresh':
                self.server.session.refresh(); self.reply(200, {'ok':True})
            else:
                self.reply(404, {'error':'Not found'})
        except FileExistsError as error:
            self.reply(409, {'error':str(error)})
        except (ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
            self.reply(400, {'error':str(error)})

    def log_message(self, *args):
        pass


def make_server(session, port=0, decoder=None):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.session, server.token = session, secrets.token_urlsafe(32)
    server.authority = '127.0.0.1:'+str(server.server_port)
    server.assets = {'/':(ASSETS/'index.html','text/html; charset=utf-8')}
    for name in ['app.js','preview-worker.js']:
        server.assets['/'+name] = (ASSETS/name,'text/javascript; charset=utf-8')
    server.assets['/icon.svg'] = (ASSETS/'icon.svg','image/svg+xml')
    if decoder:
        server.assets['/canvas-frame.wasm'] = (decoder,'application/wasm')
        server.assets['/capture-worker.js'] = (ROOT/'tools/re/browser-preview/worker.js','text/javascript; charset=utf-8')
    return server


def find_llvm():
    """Prefer a real LLVM tool pair; a Swiftly command shim cannot act as ld."""
    bins = []
    if os.environ.get('LLVM_BIN'):
        bins.append(Path(os.environ['LLVM_BIN']))
    clang = shutil.which('clang')
    if clang and '.swiftly' not in Path(clang).parts:
        bins.append(Path(clang).parent)
    bins += sorted((Path.home()/'Library/Developer/Toolchains').glob('*.xctoolchain/usr/bin'), reverse=True)
    bins += [Path('/opt/homebrew/opt/llvm/bin'), Path('/usr/local/opt/llvm/bin'), Path('/usr/bin')]
    for folder in bins:
        if (folder/'clang').is_file() and (folder/'wasm-ld').is_file():
            return str(folder/'clang'), str(folder/'wasm-ld')
    return clang, shutil.which('wasm-ld')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('--port', type=int, default=0)
    p.add_argument('--work-dir', type=Path); default_clang, default_ld = find_llvm()
    p.add_argument('--clang', default=default_clang)
    p.add_argument('--wasm-ld', default=default_ld); p.add_argument('--node', default=shutil.which('node'))
    p.add_argument('--native-factory', help='Optional Mac public ImageRenderer factory; no simulator, no private registry offsets')
    p.add_argument('--width', type=int, default=600); p.add_argument('--height', type=int, default=400)
    p.add_argument('--target'); p.add_argument('--title')
    p.add_argument('--interactive',action='store_true',default=True,help='Owned persistent AppKit host with native mouse input; Mac SwiftUI only')
    p.add_argument('--snapshot',action='store_false',dest='interactive',help='Use public ImageRenderer snapshots instead of native input')
    a = p.parse_args()
    work = a.work_dir or Path.home()/'.cache/libre-canvas'/sha(str(a.source.resolve()).encode())[:16]
    source,extra_sources,project=resolve_source(a.source,a.native_factory or 'makePreview',a.target)
    title=a.title
    if title is None:
        import re
        match=re.search(r'#Preview\(\s*"([^"\n]+)"',source.read_text())
        title=match.group(1) if match else source.stem
    session = Session(source, work, factory=a.native_factory, interactive=a.interactive and bool(a.native_factory), width=a.width, height=a.height,
                      extra_sources=extra_sources,project=project,title=title,
                      clang=a.clang, wasm_ld=a.wasm_ld, node=a.node)
    decoder = None
    if a.native_factory:
        target = work/'decoder'; target.mkdir(parents=True, exist_ok=True)
        subprocess.run([shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo'), 'rustc', '--offline', '--locked',
                        '--manifest-path', str(ROOT/'tools/re/rust/canvas-core/Cargo.toml'),
                        '--target-dir', str(target), '--target', 'wasm32-wasip1', '--bin', 'canvas-frame',
                        '--', '-C', 'link-arg=--max-memory=268435456'], check=True, timeout=90)
        decoder = target/'wasm32-wasip1/debug/canvas-frame.wasm'
    server = make_server(session, a.port, decoder); session.start()
    print(json.dumps({'url':'http://'+server.authority, 'source':str(session.source),
                      'backend':session.state['backend']}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close(); session.close()


if __name__ == '__main__':
    main()
