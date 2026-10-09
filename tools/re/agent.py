#!/usr/bin/env python3
"""Free local RE controller, CLI and MCP entry point."""
import argparse
import contextlib
import importlib.util
import json
import pathlib
import shutil
import signal
import subprocess
import sys

from reloop.core import ROOT,Controller,atomic,load,validate_queue,validate_experiment

QUEUE=ROOT/'research/loop/experiments.json'


def doctor():
    from reloop.worker import ghidra_config
    from reloop.ghidra import http
    home,java,config=ghidra_config()
    capabilities={}
    for name in ['xcodebuild','xcrun','nm','otool','codesign','git','node']:
        capabilities[name]={'installed':shutil.which(name) is not None,'path':shutil.which(name)}
    capabilities['frida']={'installed':importlib.util.find_spec('frida') is not None}
    capabilities['ghidra']={'installed':bool(home and pathlib.Path(home).is_dir()),'home':home,'java_home':java}
    for name,url in [('ghidra_engine',config.get('ghidra_engine_url','http://127.0.0.1:8089')),
                     ('ghidra_vibe',config.get('ghidra_vibe_url','http://127.0.0.1:8092'))]:
        try:capabilities[name]={'reachable':True,'response':http(url,'vibe_health',{}) if name=='ghidra_vibe' else http(url,'check_connection')}
        except Exception as error:capabilities[name]={'reachable':False,'error':str(error)}
    return {'capabilities':capabilities,'paid_services_required':False}


def read_queue(path=QUEUE):return validate_queue(load(path))


def serve(controller):
    from reloop.core import identity
    definitions=[
        ('re_doctor','Inspect local free-tool availability and Ghidra health.',{}),
        ('re_status','Read the experiment checkpoint.',{}),
        ('re_report','Build a summary candidate from verified runs without publishing raw evidence.',{}),
        ('re_next','List ready experiments after identity and evidence verification.',{}),
        ('re_run','Run one ready, reviewed experiment with time and artifact limits.',{'experiment_id':{'type':'string'}}),
        ('re_verify','Verify sealed run artifact hashes.',{'run_id':{'type':'string'}}),
        ('re_propose','Add a bounded experiment using an allowlisted adapter; no arbitrary shell commands.',{'experiment':{'type':'object'}})]
    tools=[{'name':n,'description':d,'inputSchema':{'type':'object','properties':p,'required':list(p),'additionalProperties':False}} for n,d,p in definitions]
    def tool(name,args):
        definition=next((t for t in tools if t['name']==name),None)
        if definition is None:raise ValueError('unknown tool')
        if set(args)!=set(definition['inputSchema']['required']):raise ValueError('invalid arguments')
        if name=='re_doctor':return doctor()
        if name=='re_status':return controller.status()
        if name=='re_report':
            from reloop.report import report
            return report(controller)
        if name=='re_verify':return controller.verify(args['run_id'])
        if name=='re_next':return controller.ready(read_queue(),controller.status(),identity())
        if name=='re_run':return controller.session(read_queue(),max_experiments=1,minutes=10,only=args['experiment_id'])
        if name=='re_propose':
            validate_experiment(args['experiment'])
            with controller.lock():
                q=read_queue();q['experiments'].append(args['experiment']);validate_queue(q);atomic(QUEUE,q)
            return {'proposed':args['experiment']['id'],'execution_started':False}
    for line in sys.stdin:
        request=None
        try:
            request=json.loads(line)
            if not isinstance(request,dict) or request.get('jsonrpc')!='2.0':raise ValueError('invalid JSON-RPC request')
            method=request.get('method');rid=request.get('id')
            if 'id' not in request:continue
            if method=='initialize':result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'xcpreviewer-reloop','version':'0.1.0'}}
            elif method=='ping':result={}
            elif method=='tools/list':result={'tools':tools}
            elif method=='tools/call':
                try:
                    p=request['params']
                    with contextlib.redirect_stdout(sys.stderr):value=tool(p['name'],p.get('arguments',{}))
                    result={'content':[{'type':'text','text':json.dumps(value)}],'isError':False}
                except Exception as error:result={'content':[{'type':'text','text':str(error)}],'isError':True}
            else:
                print(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not found'}}),flush=True);continue
            print(json.dumps({'jsonrpc':'2.0','id':rid,'result':result}),flush=True)
        except Exception as error:
            print(json.dumps({'jsonrpc':'2.0','id':request.get('id') if isinstance(request,dict) else None,'error':{'code':-32600,'message':str(error)}}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=pathlib.Path)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['doctor','status','serve','next','report']:sub.add_parser(name)
    run=sub.add_parser('run');run.add_argument('--queue',type=pathlib.Path,default=QUEUE);run.add_argument('--only');run.add_argument('--max-experiments',type=int,default=8);run.add_argument('--minutes',type=float,default=45);run.add_argument('--max-mb',type=int,default=1024)
    service=sub.add_parser('services');service.add_argument('action',choices=['start','stop','status'])
    verify=sub.add_parser('verify');verify.add_argument('run_id')
    args=parser.parse_args();controller=Controller(state_root=args.state_dir)
    def interrupted(signum,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    if args.command=='serve':serve(controller);return 0
    if args.command=='services':
        from reloop.services import services
        if args.action=='status':result=services(args.action)
        else:
            with controller.lock():result=services(args.action)
    elif args.command=='doctor':result=doctor()
    elif args.command=='status':result=controller.status()
    elif args.command=='report':
        from reloop.report import report
        result=report(controller)
    elif args.command=='next':
        from reloop.core import identity
        result=controller.ready(read_queue(),controller.status(),identity())
    elif args.command=='verify':result=controller.verify(args.run_id)
    else:result=controller.session(read_queue(args.queue),args.max_experiments,args.minutes,args.max_mb,args.only)
    print(json.dumps(result,indent=2))
    if args.command=='verify':return 0 if result['valid'] else 1
    if args.command=='run':return 0 if all(r['execution']=='success' and r['verdict']=='supports' for r in result) else 2
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,RuntimeError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
