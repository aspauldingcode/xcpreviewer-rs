"""Owned actual-browser alpha readback; never synthesize browser evidence in Node."""
import base64
import http.server
import json
import pathlib
import threading
import time
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.portablealpha import expected,CASES,CAPACITY

RUN='20261010T171800Z-portable-alpha-rendering-control-8b44b123'
ANCHOR='ed45a9708266d9e670605d12a1984f75343e8173bcc3b0a4f6a12e1c09b00a56'


def inspect(report,jobs,nonce,repeat,origin,module_hash):
    if report.get('nonce')!=nonce or type(report.get('repeat')) is not int or report['repeat']!=repeat:raise ValueError('Stale alpha report')
    if report.get('origin')!=origin or not isinstance(report.get('user_agent'),str) or not report['user_agent']:raise ValueError('Browser identity absent')
    if report.get('module_sha256')!=module_hash or type(report.get('imports')) is not int or report['imports']!=0:raise ValueError('Module identity mismatch')
    rows=report.get('rows');payloads={};allocation_bytes=invalid_bytes=canvas_bytes=native_bytes=0
    if not isinstance(rows,list) or len(rows)!=len(jobs):raise ValueError('Alpha browser inventory')
    for row,job in zip(rows,jobs):
        index=job['index'];n=job['n'];bg=job['bg'];raw=job['expected'];active=b''.join(raw[y*80:y*80+68] for y in range(9))
        for key,value in {'index':index,'n':n,'bg':bg,'capacity':CAPACITY,'rendered':720}.items():
            if type(row.get(key)) is not int or row[key]!=value:raise ValueError('Alpha metadata')
        if base64.b64decode(row['allocation'],validate=True)!=raw:raise ValueError('Alpha allocation mismatch')
        payloads['allocation-%d'%index]=raw;allocation_bytes+=len(raw)
        requests=[[17,9,67,n,bg],[17,9,257,n,bg],[17,9,80,9,bg],[17,9,80,n,2]]
        invalid=row['invalid']
        if not isinstance(invalid,list) or len(invalid)!=4:raise ValueError('Invalid alpha inventory')
        for k,(item,args) in enumerate(zip(invalid,requests)):
            if item.get('args')!=args or any(type(v) is not int for v in item['args']) or type(item.get('result')) is not int or item['result']!=0:raise ValueError('Invalid alpha request accepted')
            after=base64.b64decode(item['allocation'],validate=True)
            if after!=raw:raise ValueError('Invalid alpha changed allocation')
            payloads['invalid-%d-%d'%(index,k)]=after;invalid_bytes+=len(after)
        context=row.get('context',{})
        if context.get('alpha') is not True or context.get('colorSpace')!='srgb' or row.get('image_color_space')!='srgb':raise ValueError('Canvas alpha/color space changed')
        canvas=base64.b64decode(row['canvas'],validate=True)
        if canvas!=active:raise ValueError('Alpha Canvas2D readback mismatch')
        payloads['canvas-%d'%index]=canvas;canvas_bytes+=len(canvas)
        if job.get('native') is not None:
            if canvas!=job['native']:raise ValueError('Native alpha mismatch')
            native_bytes+=len(canvas)
    return {'payloads':payloads,'allocation_bytes':allocation_bytes,'invalid_bytes':invalid_bytes,'canvas_bytes':canvas_bytes,'native_bytes':native_bytes}


def corpus(out):
    out=pathlib.Path(out);c=Controller(root=PROJECT_ROOT)
    if not c.verify(RUN,ANCHOR)['valid']:raise ValueError('Portable alpha anchor mismatch')
    source=c.runs/RUN/'output';module=source/'alpha.wasm';module_hash=digest(module);jobs=[]
    for row in load(source/'execution.json')['rows']:
        if row['stride']!=80 or row['repeat']!=0:continue
        raw=expected(17,9,80,row['n'],row['bg'])
        if (source/('frame-%d.rgba'%row['index'])).read_bytes()!=raw:raise ValueError('Anchored alpha allocation mismatch')
        native=(source/('native-%d.rgba'%CASES.index((row['n'],row['bg'])))).read_bytes() if (row['n'],row['bg']) in CASES else None
        jobs.append({'index':len(jobs),'n':row['n'],'bg':row['bg'],'expected':raw,'native':native})
    if len(jobs)!=18:raise ValueError('Anchored alpha job inventory')
    public_jobs=[{k:j[k] for k in ('index','n','bg')} for j in jobs]
    template=(ROOT/'tools/re/reloop/browser_alpha.html').read_text();nonce=uuid.uuid4().hex;reports=[];errors=[];lock=threading.Lock()
    origin=None
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/':
                with lock:repeat=len(reports)
                data=template.replace('__CONFIG__',json.dumps({'jobs':public_jobs,'nonce':nonce,'repeat':repeat})).encode();mime='text/html'
            elif self.path=='/alpha.wasm':data=module.read_bytes();mime='application/wasm'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if self.path!='/result' or not 0<size<8*1024*1024:raise ValueError('Report bounds')
                self.connection.settimeout(10);report=json.loads(self.rfile.read(size))
                with lock:
                    index=len(reports)
                    atomic(out/('received-%d.json'%index),report) # Retain rejected actual observations too.
                    if index>=2:raise ValueError('Extra report')
                    checked=inspect(report,jobs,nonce,index,origin,module_hash)
                    folder=out/('repeat-%d'%index);folder.mkdir()
                    for key,raw in checked['payloads'].items():(folder/(key+'.bin')).write_bytes(raw)
                    reports.append({**checked,'user_agent':report['user_agent']})
                self.send_response(200);self.end_headers();self.wfile.write(b'accepted')
            except Exception as error:
                with lock:errors.append(str(error))
                self.send_error(400,str(error))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    origin='http://127.0.0.1:%d'%server.server_port
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    atomic(out/'browser-endpoint.json',{'url':origin+'/','nonce':nonce,'deadline_seconds':120})
    atomic(out/'source-anchor.json',{'run_id':RUN,'manifest_sha256':ANCHOR,'module_sha256':module_hash})
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            with lock:done=len(reports)==2;failed=bool(errors)
            if done or failed:break
            time.sleep(.1)
        if errors:raise ValueError('Browser alpha report: '+errors[0])
        if len(reports)!=2:raise TimeoutError('Two actual alpha browser loads required')
        if reports[0]['payloads']!=reports[1]['payloads']:raise ValueError('Alpha browser repeat differs')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
        cleanup={'closed':server.socket.fileno()==-1,'thread_stopped':not thread.is_alive(),'errors':errors}
        atomic(out/'server-cleanup.json',cleanup)
        if not cleanup['closed'] or not cleanup['thread_stopped']:raise RuntimeError('Owned browser server cleanup incomplete')
    return {'browser_frames':36,'browser_repeats':2,**{k:sum(r[k] for r in reports) for k in ('allocation_bytes','invalid_bytes','canvas_bytes','native_bytes')},'user_agent':reports[0]['user_agent'],'server_cleanup':True,'scope':'Actual macOS in-app browser anchored alpha WASM; alpha-enabled sRGB Canvas2D straight readback. Eight native cases, remaining model controls. No source frontend, arbitrary colors/linear modes/Canvas wire/platform/cost claim.'}
