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
CAMPAIGN=ROOT/'research/loop/campaign.json'


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

def all_queue():
    a=read_queue();b=read_queue(CAMPAIGN)
    return validate_queue({'version':1,'experiments':a['experiments']+b['experiments']})


def serve(controller):
    from reloop.core import identity
    definitions=[
        ('re_verify_anchor','Verify sealed artifacts and a separately trusted manifest SHA-256.',{'run_id':{'type':'string'},'manifest_sha256':{'type':'string'}}),
        ('re_compare','Compare every byte of two verified sealed artifacts, without normalization.',{'reference':{'type':'object'},'candidate':{'type':'object'}}),
        ('re_index','Index verified runs for local search and evidence links.',{}),
        ('re_search','Search verified evidence; returns small snippets and artifact references.',{'query':{'type':'string'}}),
        ('re_graph','Get bounded runtime/static evidence links for a sealed run.',{'run_id':{'type':'string'}}),
        ('re_artifact','Read a verified artifact page; offset and chars count Unicode characters.',{'run_id':{'type':'string'},'path':{'type':'string'},'offset':{'type':'integer'},'chars':{'type':'integer'}}),
        ('re_response','Read an exact page from a bounded tool response.',{'response_id':{'type':'string'},'offset':{'type':'integer'},'chars':{'type':'integer'}}),
        ('re_claim','Assess an explicitly scoped claim against sealed observation checks.',{'claim':{'type':'object'}}),
        ('re_plan','Suggest discriminating counterexperiments from verified outcomes.',{}),
        ('re_engine_tools','Discover allowlisted live Ghidra engine tool contracts.',{}),
        ('re_engine_read','Query explicit Ghidra program: symbols, references, decompilation, disassembly.',{'operation':{'type':'string'},'arguments':{'type':'object'}}),
        ('re_campaign','Run up to four connected campaign experiments with a 15-minute budget.',{}),
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
        if name=='re_verify_anchor':return controller.verify(args['run_id'],args['manifest_sha256'])
        if name=='re_compare':
            from reloop.verification import sealed_compare
            return sealed_compare(controller,args['reference'],args['candidate'])
        if name in {'re_index','re_search','re_graph'}:
            from reloop.evidence import Store
            store=Store(controller)
            try:
                with controller.lock():
                    if name=='re_index':return store.index()
                    if name=='re_search':return store.search(args['query'])
                    return store.graph(args['run_id'])
            finally:store.close()
        if name=='re_artifact':
            from reloop.evidence import page
            return page(controller,args['run_id'],args['path'],args['offset'],args['chars'])
        if name=='re_response':
            from reloop.responses import page
            return page(controller,args['response_id'],args['offset'],args['chars'])
        if name=='re_claim':
            from reloop.evidence import claim
            with controller.lock():return claim(controller,args['claim'])
        if name=='re_plan':
            from reloop.planner import plan
            return plan(controller)
        if name=='re_engine_tools':
            from reloop.engine import catalog
            return catalog()
        if name=='re_engine_read':
            from reloop.engine import dispatch,READ_TOOLS
            if args['operation'] not in READ_TOOLS:raise ValueError('Read-only operation required')
            with controller.lock():return dispatch(args['operation'],args['arguments'])
        if name=='re_campaign':return controller.session(read_queue(CAMPAIGN),4,15)
        if name=='re_doctor':return doctor()
        if name=='re_status':return controller.status()
        if name=='re_report':
            from reloop.report import report
            return report(controller)
        if name=='re_verify':return controller.verify(args['run_id'])
        if name=='re_next':return controller.ready(all_queue(),controller.status(),identity())
        if name=='re_run':return controller.session(all_queue(),max_experiments=1,minutes=10,only=args['experiment_id'])
        if name=='re_propose':
            validate_experiment(args['experiment'])
            with controller.lock():
                q=read_queue(CAMPAIGN);q['experiments'].append(args['experiment']);validate_queue({'version':1,'experiments':read_queue()['experiments']+q['experiments']});atomic(CAMPAIGN,q)
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
                    from reloop.responses import bounded
                    if p['name'] not in {'re_response','re_artifact'}:value=bounded(controller,value)
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
    for name in ['doctor','status','serve','next','report','index','plan','campaign']:sub.add_parser(name)
    run=sub.add_parser('run');run.add_argument('--queue',type=pathlib.Path,default=QUEUE);run.add_argument('--only');run.add_argument('--max-experiments',type=int,default=8);run.add_argument('--minutes',type=float,default=45);run.add_argument('--max-mb',type=int,default=1024)
    search=sub.add_parser('search');search.add_argument('query')
    claim_parser=sub.add_parser('claim');claim_parser.add_argument('spec',type=pathlib.Path)
    service=sub.add_parser('services');service.add_argument('action',choices=['start','stop','status'])
    verify=sub.add_parser('verify');verify.add_argument('run_id');verify.add_argument('--manifest-sha256')
    compare=sub.add_parser('compare');compare.add_argument('reference_run');compare.add_argument('reference_path');compare.add_argument('candidate_run');compare.add_argument('candidate_path')
    args=parser.parse_args();controller=Controller(state_root=args.state_dir)
    def interrupted(signum,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    if args.command=='serve':serve(controller);return 0
    if args.command=='campaign':result=controller.session(read_queue(CAMPAIGN),4,15)
    elif args.command=='compare':
        from reloop.verification import sealed_compare
        result=sealed_compare(controller,{'run_id':args.reference_run,'path':args.reference_path},
                              {'run_id':args.candidate_run,'path':args.candidate_path})
    elif args.command in {'index','search'}:
        from reloop.evidence import Store
        store=Store(controller)
        try:
            with controller.lock():result=store.index() if args.command=='index' else store.search(args.query)
        finally:store.close()
    elif args.command=='claim':
        from reloop.evidence import claim
        with controller.lock():result=claim(controller,load(args.spec))
    elif args.command=='plan':
        from reloop.planner import plan
        result=plan(controller)
    elif args.command=='services':
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
        result=controller.ready(all_queue(),controller.status(),identity())
    elif args.command=='verify':result=controller.verify(args.run_id,args.manifest_sha256)
    else:result=controller.session(read_queue(args.queue),args.max_experiments,args.minutes,args.max_mb,args.only)
    print(json.dumps(result,indent=2))
    if args.command=='verify':return 0 if result['valid'] else 1
    if args.command=='compare':return 0 if result['passed'] else 1
    if args.command in {'run','campaign'}:return 0 if all(r['execution']=='success' and r['verdict']=='supports' for r in result) else 2
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,RuntimeError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
