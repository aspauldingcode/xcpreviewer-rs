"""Actual-browser source-derived WASM and explicit premultiplied Canvas2D boundary."""
import base64
import http.server
import json
import pathlib
import re
import threading
import time
import uuid
from reloop.core import Controller,PROJECT_ROOT,ROOT,atomic,digest,load
from reloop.primarysource import expected,validate,parse
RUN='20261010T191804Z-portable-primary-source-subset-811cf568'
ANCHOR='45f7ac0b391eb74b2580209a237e231ee77d55be31c2857129c14137d69b3f88'


def straight(raw,config,stride):
    active=bytearray()
    for y in range(config['height']):
        for x in range(config['width']):
            p=raw[y*stride+x*4:y*stride+x*4+4];a=p[3]
            active.extend((2*c*255+a)//(2*a) if a else 0 for c in p[:3]);active.append(a)
    return bytes(active)


def inspect(report,jobs,checkers,nonce,repeat,origin,source):
    if report.get('nonce')!=nonce or type(report.get('repeat')) is not int or report['repeat']!=repeat:raise ValueError('Stale source browser report')
    if report.get('origin')!=origin or type(report.get('user_agent')) is not str or not report['user_agent']:raise ValueError('Browser identity absent')
    if type(report.get('imports')) is not int or report['imports']!=0:raise ValueError('Browser source imports')
    if report.get('renderer_hashes')!=[j['module_sha256'] for j in jobs] or report.get('checker_hashes')!=[j['module_sha256'] for j in checkers]:raise ValueError('Browser source module identity')
    rows=report.get('rows');invalid=report.get('invalid');controls=report.get('controls');aggregates=report.get('aggregates');negative=report.get('checker_invalid')
    for entries,n in ((rows,64),(invalid,64),(controls,160),(aggregates,16),(negative,64)):
        if type(entries) is not list or len(entries)!=n or any(type(row) is not dict for row in entries):raise ValueError('Browser source inventory')
    payloads={};allocation_bytes=canvas_bytes=native_bytes=invalid_bytes=0;wanted_controls=[];wanted_aggregates=[];wanted_negative=[]
    for i,job in enumerate(jobs):
        cfg=job['config'];validate(cfg)
        for s,stride in enumerate(job['strides']):
            raw=expected(cfg,stride);converted=straight(raw,cfg,stride)
            for repeat_index in range(2):
                row=rows[i*4+s*2+repeat_index]
                for k,v in {'job':i,'stride_index':s,'repeat':repeat_index,'capacity':16384,'rendered':stride*cfg['height']}.items():
                    if type(row.get(k)) is not int or row[k]!=v:raise ValueError('Browser source frame metadata')
                actual=base64.b64decode(row['allocation'],validate=True)
                if actual!=raw or actual!=(source/('frame-%d-%d-%d.raw'%(i,s,repeat_index))).read_bytes():raise ValueError('Browser source allocation mismatch')
                if base64.b64decode(row['straight'],validate=True)!=converted:raise ValueError('Explicit straight conversion mismatch')
                context=row.get('context',{})
                if context.get('alpha') is not True or context.get('colorSpace')!='srgb' or row.get('image_color_space')!='srgb':raise ValueError('Source Canvas2D context')
                canvas=base64.b64decode(row['canvas'],validate=True)
                if canvas!=converted:raise ValueError('Source Canvas2D roundtrip mismatch')
                key='frame-%d-%d-%d'%(i,s,repeat_index);payloads[key]=actual;payloads[key+'-canvas']=canvas
                allocation_bytes+=len(actual);canvas_bytes+=len(canvas)
                if (cfg['width'],cfg['height'],stride)==(17,9,80):
                    if actual!=(source/('native-%d-%d-%d.raw'%(i,s,repeat_index))).read_bytes():raise ValueError('Source native callback prefix mismatch')
                    native_bytes+=720
        for k,stride in enumerate((0,cfg['width']*4-1,257,0xffffffff)):
            row=invalid[i*4+k]
            for key,value in {'job':i,'index':k,'stride':stride,'result':0}.items():
                if type(row.get(key)) is not int or row[key]!=value:raise ValueError('Invalid browser source request')
            raw=base64.b64decode(row['allocation'],validate=True)
            if raw!=expected(cfg,job['strides'][0]):raise ValueError('Invalid browser source writes')
            payloads['invalid-%d-%d'%(i,k)]=raw;invalid_bytes+=len(raw)
        wanted_controls.extend({'job':i,'stride_index':s,'mutation':m,'count':1 if m else 0} for s in range(2) for m in range(5))
        wanted_aggregates.append({'job':i,'count':8})
        wanted_negative.extend({'job':i,'index':k,'stride_index':s,'mutation':m,'count':0xffffffff} for k,(s,m) in enumerate(((2,0),(0,5),(0xffffffff,0),(0,0xffffffff))))
    for records,keys in ((controls,('job','stride_index','mutation','count')),(aggregates,('job','count')),(negative,('job','index','stride_index','mutation','count'))):
        if any(any(type(r.get(k)) is not int for k in keys) for r in records):raise ValueError('Browser checker integer metadata')
    if controls!=wanted_controls or aggregates!=wanted_aggregates or negative!=wanted_negative:raise ValueError('Browser source checker disagreement')
    return {'payloads':payloads,'allocation_bytes':allocation_bytes,'canvas_bytes':canvas_bytes,'native_bytes':native_bytes,'invalid_bytes':invalid_bytes}


def corpus(out):
    out=pathlib.Path(out);c=Controller(root=PROJECT_ROOT);v=c.verify(RUN,ANCHOR)
    if not v['valid'] or not v['external_anchor_matches']:raise ValueError('Primary source anchor mismatch')
    source=c.runs/RUN/'output';jobs=load(source/'jobs.json');checkers=load(source/'wasmkit.json')
    if len(jobs)!=16 or len(checkers)!=16:raise ValueError('Source module inventory')
    for i,j in enumerate(jobs):
        if parse((source/('source-%d.swift'%i)).read_text())!=j['config'] or digest(source/('source-%d.ll'%i))!=j['ir_sha256'] or digest(source/('source-%d.wasm'%i))!=j['module_sha256'] or digest(source/('checker-%d.wasm'%i))!=checkers[i]['module_sha256']:raise ValueError('Source/config/IR/module identity')
    template=(ROOT/'tools/re/reloop/browser_primary_source.html').read_text();nonce=uuid.uuid4().hex;reports=[];errors=[];lock=threading.Lock();origin=None
    public=[{k:j[k] for k in ('index','config','strides')} for j in jobs]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/':
                with lock:index=len(reports)
                data=template.replace('__CONFIG__',json.dumps({'jobs':public,'nonce':nonce,'repeat':index})).encode();mime='text/html'
            elif re.fullmatch(r'/(?:source|checker)-(?:[0-9]|1[0-5])\.wasm',self.path):data=(source/self.path[1:]).read_bytes();mime='application/wasm'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if self.path!='/result' or not 0<size<8*1024*1024:raise ValueError('Source report bounds')
                self.connection.settimeout(10);report=json.loads(self.rfile.read(size))
                with lock:
                    index=len(reports);atomic(out/('received-%d.json'%index),report)
                    if index>=2:raise ValueError('Extra source report')
                    checked=inspect(report,jobs,checkers,nonce,index,origin,source);folder=out/('repeat-%d'%index);folder.mkdir()
                    for key,raw in checked['payloads'].items():(folder/(key+'.raw')).write_bytes(raw)
                    reports.append({**checked,'user_agent':report['user_agent']})
                self.send_response(200);self.end_headers();self.wfile.write(b'accepted')
            except Exception as error:
                with lock:errors.append(str(error))
                self.send_error(400,str(error))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;origin='http://127.0.0.1:%d'%server.server_port
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();atomic(out/'browser-endpoint.json',{'url':origin+'/','nonce':nonce,'deadline_seconds':120});atomic(out/'source-anchor.json',v)
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            with lock:done=len(reports)==2;failed=bool(errors)
            if done or failed:break
            time.sleep(.1)
        if errors:raise ValueError('Browser source report: '+errors[0])
        if len(reports)!=2:raise TimeoutError('Two actual source browser loads required')
        if reports[0]['payloads']!=reports[1]['payloads']:raise ValueError('Browser source repeat differs')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2);cleanup={'closed':server.socket.fileno()==-1,'thread_stopped':not thread.is_alive(),'errors':errors};atomic(out/'server-cleanup.json',cleanup)
        if not cleanup['closed'] or not cleanup['thread_stopped']:raise RuntimeError('Source browser server cleanup incomplete')
    return {'browser_modules':16,'browser_frames':128,'browser_repeats':2,'checker_controls':320,'mutation_controls':256,'aggregate_controls':32,'invalid_checker_requests':128,**{k:sum(r[k] for r in reports) for k in ('allocation_bytes','invalid_bytes','canvas_bytes','native_bytes')},'user_agent':reports[0]['user_agent'],'server_cleanup':True,'scope':'Actual macOS browser exact pinned source-derived WASM and explicit premultiplied-to-straight sRGB Canvas2D roundtrip; complete independent/native callback targets. Native getter/PNG differs. Frontend remains macOS; no arbitrary SwiftUI, Canvas wire, Windows or cost claim.'}
