"""Serve the local bitmap preview UI; no file upload or external hosting service."""
from pathlib import Path
import argparse,http.server,json,os,shutil,subprocess,tempfile,urllib.parse
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);p.add_argument('--wasm',type=Path);p.add_argument('--sample',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[2]
if a.wasm:wasm=a.wasm.resolve()
else:
 target=Path(tempfile.mkdtemp(prefix='canvas-preview-'));cargo=shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo')
 subprocess.run([cargo,'rustc','--offline','--locked','--manifest-path',str(repo/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(target),'--target','wasm32-wasip1','--bin','canvas-frame','--','-C','link-arg=--max-memory=268435456'],check=True,timeout=60)
 wasm=target/'wasm32-wasip1/debug/canvas-frame.wasm'
assert wasm.is_file(),'Build canvas-frame for wasm32-wasip1 first'
sample=a.sample.resolve() if a.sample else here/'sample.bplist'
assert sample.is_file() and sample.stat().st_size<=64*1024*1024,'Sample must be a file of at most 64 MiB'
routes={'/':(here/'index.html','text/html; charset=utf-8'),'/index.html':(here/'index.html','text/html; charset=utf-8'),'/viewer.js':(here/'viewer.js','text/javascript; charset=utf-8'),'/worker.js':(here/'worker.js','text/javascript; charset=utf-8'),'/sample-follow.js':(here/'sample-follow.js','text/javascript; charset=utf-8'),'/sample.bplist':(sample,'application/octet-stream'),'/canvas-frame.wasm':(wasm,'application/wasm')}
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  item=routes.get(urllib.parse.urlsplit(self.path).path)
  if not item:self.send_error(404);return
  with item[0].open('rb') as stream:data=stream.read(64*1024*1024+1)
  if len(data)>64*1024*1024:self.send_error(413);return
  self.send_response(200);self.send_header('Content-Type',item[1]);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'");self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler);print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/'}),flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
