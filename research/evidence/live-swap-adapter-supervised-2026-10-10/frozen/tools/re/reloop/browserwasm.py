"""Actual browser page run via existing UI tools; loopback server stays under controller lock."""
import base64
import http.server
import json
import pathlib
import threading
import time
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.linuxwasm import RUN,ANCHOR

CAPACITY=204800

def inspect(report,jobs,nonce,repeat,source):
    if report.get('nonce')!=nonce or type(report.get('repeat')) is not int or report['repeat']!=repeat:raise ValueError('Stale browser report')
    if not isinstance(report.get('user_agent'),str) or not report['user_agent'] or not report.get('origin','').startswith('http://127.0.0.1:'):raise ValueError('Browser identity absent')
    rows=report.get('rows');payloads={};compared=invalid_bytes=canvas_bytes=0
    if not isinstance(rows,list) or len(rows)!=4:raise ValueError('Browser inventory')
    for row,job in zip(rows,jobs):
        i=job['index'];cfg=job['config'];stride=job['stride'];n=stride*cfg['height']
        for key,value in {'index':i,'imports':0,'capacity':CAPACITY,'rendered':n}.items():
            if type(row.get(key)) is not int or row[key]!=value:raise ValueError('Browser metadata')
        if row['module_sha256']!=job['module_sha256']:raise ValueError('Browser module identity')
        # Previously sealed independent native/literal pixel reference, plus predicted untouched allocation tail.
        expected=(source/('pixels-%d.rgba'%i)).read_bytes()+bytes([0xa5])*(CAPACITY-n)
        raw=base64.b64decode(row['allocation'],validate=True)
        if raw!=expected:raise ValueError('Browser allocation mismatch')
        payloads['allocation-%d'%i]=raw;compared+=len(raw)
        invalid=row['invalid'];expected_strides=[0,cfg['width']*4-1,1281,0xffffffff]
        if not isinstance(invalid,list) or len(invalid)!=4:raise ValueError('Invalid request inventory')
        for k,(item,bad) in enumerate(zip(invalid,expected_strides)):
            if type(item.get('stride')) is not int or item['stride']!=bad or type(item.get('result')) is not int or item['result']!=0:raise ValueError('Invalid stride accepted')
            after=base64.b64decode(item['allocation'],validate=True)
            if after!=expected:raise ValueError('Invalid request changed allocation')
            payloads['invalid-%d-%d'%(i,k)]=after;invalid_bytes+=len(after)
        active=b''.join(expected[y*stride:y*stride+cfg['width']*4] for y in range(cfg['height']))
        actual=base64.b64decode(row['canvas'],validate=True)
        if actual!=active:raise ValueError('Canvas2D readback mismatch')
        payloads['canvas-%d'%i]=actual;canvas_bytes+=len(actual)
    return {'payloads':payloads,'allocation_bytes':compared,'invalid_bytes':invalid_bytes,'canvas_bytes':canvas_bytes}


def corpus(out):
    out=pathlib.Path(out);c=Controller(root=PROJECT_ROOT)
    if not c.verify(RUN,ANCHOR)['valid']:raise ValueError('Browser source anchor mismatch')
    source=c.runs/RUN/'output';jobs=load(source/'jobs.json');nonce=uuid.uuid4().hex;reports=[];errors=[];lock=threading.Lock()
    template=(ROOT/'tools/re/reloop/browser_source.html').read_text()
    for job in jobs:
        if digest(source/('source-%d.wasm'%job['index']))!=job['module_sha256']:raise ValueError('Source module changed')
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/':
                with lock:repeat=len(reports)
                data=template.replace('__CONFIG__',json.dumps({'jobs':jobs,'nonce':nonce,'repeat':repeat})).encode();mime='text/html'
            elif self.path in ['/source-%d.wasm'%i for i in range(4)]:data=(source/self.path[1:]).read_bytes();mime='application/wasm'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if self.path!='/result' or not 0<size<8*1024*1024:raise ValueError('Report bounds')
                self.connection.settimeout(10);report=json.loads(self.rfile.read(size))
                with lock:
                    index=len(reports)
                    if index>=2:raise ValueError('Extra report')
                    checked=inspect(report,jobs,nonce,index,source)
                    folder=out/('repeat-%d'%index);folder.mkdir()
                    atomic(folder/'report.json',report)
                    for key,raw in checked['payloads'].items():(folder/(key+'.bin')).write_bytes(raw)
                    reports.append({**checked,'user_agent':report['user_agent']})
                self.send_response(200);self.end_headers();self.wfile.write(b'accepted')
            except Exception as error:
                with lock:errors.append(str(error))
                self.send_error(400,str(error))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    atomic(out/'browser-endpoint.json',{'url':'http://127.0.0.1:%d/'%server.server_port,'nonce':nonce,'deadline_seconds':120})
    atomic(out/'source-anchor.json',{'run_id':RUN,'manifest_sha256':ANCHOR})
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            with lock:done=len(reports)==2;failed=bool(errors)
            if done or failed:break
            time.sleep(.1)
        if errors:raise ValueError('Browser report: '+errors[0])
        if len(reports)!=2:raise TimeoutError('Two actual browser loads required')
        if reports[0]['payloads']!=reports[1]['payloads']:raise ValueError('Browser repeat differs')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
        atomic(out/'server-cleanup.json',{'closed':server.socket.fileno()==-1,'thread_stopped':not thread.is_alive(),'errors':errors})
    return {'browser_modules':4,'browser_repeats':2,'allocation_bytes':sum(r['allocation_bytes'] for r in reports),'invalid_bytes':sum(r['invalid_bytes'] for r in reports),'canvas_bytes':sum(r['canvas_bytes'] for r in reports),'user_agent':reports[0]['user_agent'],'server_cleanup':True,'scope':'Exact anchored import-free owned WASM in actual macOS in-app browser and Canvas2D readback, native/literal pixels and full allocation padding/tail. No browser source compilation, general SwiftUI, Canvas wire or performance claim.'}
