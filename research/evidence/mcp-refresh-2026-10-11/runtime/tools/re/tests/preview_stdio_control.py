"""Owned process/stdin frames and EOF drain, with bounded native subprocesses."""
import json,os,selectors,subprocess,sys,time,shutil
from pathlib import Path

def run(runtime,config,inputs,out):
    out=Path(out);out.mkdir();runtime=Path(runtime);inputs=Path(inputs);records=[]
    for mode in ['edits','eof']:
        root=out/mode;root.mkdir();source=root/'owned.swift';source.write_bytes((inputs/'0-source.swift').read_bytes());packets=[];buffer=bytearray()
        with (root/'stderr.txt').open('wb') as stderr:
            p=subprocess.Popen([shutil.which('node'),str(runtime/'tools/re/preview_stdio.js'),str(config),str(source),str(root/'builds'),'10000'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr)
            def send(i,method):p.stdin.write((json.dumps({'id':i,'method':method})+'\n').encode());p.stdin.flush()
            def receive():
                limit=time.monotonic()+6
                with selectors.DefaultSelector() as selector:
                    selector.register(p.stdout,selectors.EVENT_READ)
                    while b'\n' not in buffer:
                        assert time.monotonic()<limit,'Packet deadline'
                        assert selector.select(max(0,limit-time.monotonic())),'Packet deadline'
                        b=os.read(p.stdout.fileno(),4096);assert b,'Unexpected stdout EOF';buffer.extend(b);assert len(buffer)<=32768
                line,_,rest=buffer.partition(b'\n');buffer[:]=rest;row=json.loads(line);packets.append(row);return row
            try:
                send(1,'start')
                if mode=='edits':
                    assert receive()['ok'];send(2,'frame');assert receive()['ok']
                    source.write_bytes((inputs/'1-source.swift').read_bytes());send(3,'poll');assert receive()['ok'];send(4,'frame');assert receive()['ok']
                    source.write_bytes(b'Text("unsupported")');send(5,'poll');assert receive()['result']['diagnostics']['lastFailure']['kind']=='rejected';send(6,'frame');assert receive()['ok']
                    source.write_bytes((inputs/'2-source.swift').read_bytes());send(7,'poll');assert receive()['ok'];send(8,'frame');assert receive()['ok'];send(9,'close');assert receive()['result']['lifecycle']['loopClosed']
                p.stdin.close();code=p.wait(timeout=8);assert code==0
                trailing=p.stdout.read(32769);assert not trailing and not buffer
                lifecycle=json.loads((root/'builds/session-lifecycle.json').read_text());assert lifecycle['final']['frame'] is None and lifecycle['final']['lifecycle']['liveWorkers']==lifecycle['final']['lifecycle']['timers']==0 and lifecycle['final']['lifecycle']['building'] is False
                if mode=='eof':assert not packets and lifecycle['channel']['reason']=='input-ended' and lifecycle['channel']['cancelled']==1 and lifecycle['channel']['writes']==0
                records.append({'mode':mode,'code':code,'packets':packets,'lifecycle':lifecycle})
            finally:
                if not p.stdin.closed:p.stdin.close()
                try:p.wait(timeout=8)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2);raise
                p.stdout.close()
    (out/'result.json').write_text(json.dumps({'records':records,'scope':'Owned Node process/custom stdin protocol with actual finite Rust builds and Python byte oracle; EOF phase unlocalized; no MCP/native Canvas claim'},indent=2)+'\n')

if __name__=='__main__':run(*sys.argv[1:])
