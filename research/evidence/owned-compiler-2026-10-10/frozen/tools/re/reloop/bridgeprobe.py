"""Bounded read-only Xcode MCP route diagnostic, independent of tools/list discovery."""
import json
import os
import pathlib
import subprocess
import threading
import time
import uuid
from reloop.core import atomic
from reloop.mcp_client import Client


def summarize(events,outcome):
    sent=[e['message'].get('method') for e in events if e['direction']=='out' and 'method' in e['message']]
    reverse=[e['message']['method'] for e in events if e['direction']=='in' and 'method' in e['message'] and 'id' in e['message']]
    return {'initialized':outcome.get('initialized',False),'direct_call_completed':outcome.get('completed',False),
            'direct_call_error':outcome.get('error'),'discovery_requested':'tools/list' in sent,'server_request_methods':reverse,
            'message_count':len(events),'scope':'Read-only Xcode window-list route, not Canvas capture or IPC recovery. Local initialize response alone does not prove downstream tool responsiveness.'}


def probe(out,managed=False):
    out=pathlib.Path(out);events=[];lock=threading.Lock();client=None;state={}
    if managed:
        from reloop.xcodebridge import BrokerClient
        identities=[]
        try:
            for number in range(2):
                client=BrokerClient();identities.append(client.metadata)
                response=client.request('tools/call',{'name':'XcodeListWindows','arguments':{}})
                atomic(out/('windows-response-%d.json'%number),response)
                if response.get('isError'):raise RuntimeError('Xcode tool returned isError')
                client.close()
            same=all(x['pid']==identities[0]['pid'] and x['session_id']==identities[0]['session_id'] for x in identities)
            state.update(initialized=True,completed=True)
        except Exception as error:
            same=False;state.update(error=str(error),error_type=type(error).__name__)
        atomic(out/'broker-identities.json',identities);atomic(out/'diagnostic.json',state)
        return {**summarize(events,state),'managed_connection':True,'same_broker_session':same,
                'independent_callers_completed':2 if state.get('completed') else 0,
                'message_count':None,'server_request_methods':None,
                'transport_observation_scope':'Managed upstream messages are not traced by this caller; null is unobserved, not zero traffic.'}
    process_list=subprocess.run(['ps','-axo','pid=,comm='],capture_output=True,text=True,timeout=5,check=True).stdout
    pids=[int(line.strip().split(None,1)[0]) for line in process_list.splitlines() if line.strip().endswith('/Applications/Xcode.app/Contents/MacOS/Xcode')]
    if len(pids)!=1:raise RuntimeError('Require exactly one identified installed Xcode for read-only probe')
    env=dict(os.environ);env['MCP_XCODE_PID']=str(pids[0]);env['MCP_XCODE_SESSION_ID']=str(uuid.uuid4())
    def observer(direction,message):
        with lock:
            if len(events)>=200:raise RuntimeError('Bridge message cap exceeded')
            events.append({'direction':direction,'monotonic_ns':time.monotonic_ns(),'message':message})
    with (out/'bridge.stderr').open('wb') as stderr:
        try:
            client=Client(['xcrun','mcpbridge'],stderr,timeout=12,env=env,observer=observer)
            state['initialized']=True;atomic(out/'initialize.json',client.initialized)
            response=client.request('tools/call',{'name':'XcodeListWindows','arguments':{}})
            atomic(out/'windows-response.json',response);state['completed']=response.get('isError') is not True
            if not state['completed']:state['error']='Xcode tool returned isError'
        except Exception as error:state.update(error=str(error),error_type=type(error).__name__)
        finally:
            if client:client.close()
    atomic(out/'protocol.json',events);atomic(out/'diagnostic.json',{'xcode_pid':pids[0],**state})
    return summarize(events,state)
