"""Explicit lifecycle for local Ghidra services owned by this repository."""
import os
import pathlib
import signal
import subprocess
import sys
import time
from reloop.core import ROOT,atomic,load,now
from reloop.ghidra import http
from reloop.worker import ghidra_config


def process_identity(pid):
    r=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','command='],capture_output=True,text=True,timeout=5)
    return r.stdout.strip() if r.returncode==0 else None


def services(action):
    directory=ROOT/'research/state/services';directory.mkdir(parents=True,exist_ok=True)
    home,java,config=ghidra_config()
    if action=='status':
        result={}
        for name,url in [('engine',config.get('ghidra_engine_url','http://127.0.0.1:8089')),('vibe',config.get('ghidra_vibe_url','http://127.0.0.1:8092'))]:
            try:result[name]={'reachable':True,'health':http(url,'check_connection',timeout=2)}
            except Exception as error:result[name]={'reachable':False,'error':str(error)}
        return result
    if action=='stop':
        stopped=[]
        for name in ['vibe','engine']:
            path=directory/(name+'.json');record=load(path)
            if not record:continue
            current=process_identity(record['pid'])
            if current is None:stopped.append({'name':name,'already_exited':True});path.unlink();continue
            if current!=record['identity']:raise RuntimeError('Process ownership changed; refusing to stop '+name)
            os.killpg(record['pid'],signal.SIGTERM)
            deadline=time.monotonic()+3
            while process_identity(record['pid']) and time.monotonic()<deadline:time.sleep(.1)
            if process_identity(record['pid'])==record['identity']:os.killpg(record['pid'],signal.SIGKILL)
            path.unlink();stopped.append({'name':name,'stopped':True})
        return stopped
    if not home or not java:raise RuntimeError('Ghidra/JDK unavailable; configure research/local-config.json')
    engine_url=config.get('ghidra_engine_url','http://127.0.0.1:8089')
    vibe_url=config.get('ghidra_vibe_url','http://127.0.0.1:8092')
    from urllib.parse import urlsplit
    from reloop.ghidra import local_url
    for url in [engine_url,vibe_url]:local_url(url)
    env=dict(os.environ)
    env.update(GHIDRA_MCP_URL=engine_url,GHIDRA_VIBE_ANALYSIS_AUTOSTART='0',
               GHIDRA_VIBE_RULES=str(directory/'playbook.md'),GHIDRA_VIBE_MALIMITE_DB=str(directory/'malimite.db'))
    commands={
        'engine':[str(pathlib.Path(java)/'bin/java'),'-Xmx2G','-Djava.awt.headless=true',
                  '-Djava.system.class.loader=ghidra.GhidraClassLoader','-Dapplication.settingsdir='+str(directory/'settings'),
                  '-Djava.io.tmpdir='+str(directory/'tmp'),'-cp',str(pathlib.Path(home)/'Ghidra/Framework/Utility/lib/Utility.jar'),
                  'ghidra.Ghidra','com.xebyte.headless.GhidraMCPHeadlessServer','--bind','127.0.0.1','--port',str(urlsplit(engine_url).port or 8089)],
        'vibe':[sys.executable,'-m','vibe_mcp','--host','127.0.0.1','--port',str(urlsplit(vibe_url).port or 8092)]}
    library=pathlib.Path(home).parents[1]/'share/ghidra-vibe/lib'
    if not (library/'vibe_mcp').is_dir():
        library=pathlib.Path.home()/'GhidraVibe/scripts/lib'
    if not (library/'vibe_mcp').is_dir():raise RuntimeError('GhidraVibe extension package unavailable')
    env['PYTHONPATH']=str(library)
    (directory/'tmp').mkdir(exist_ok=True)
    started=[]
    for name,url in [('engine',engine_url),('vibe',vibe_url)]:
        try:http(url,'check_connection',timeout=1);started.append({'name':name,'already_running':True});continue
        except Exception:pass
        prior=load(directory/(name+'.json'))
        if prior and process_identity(prior['pid'])==prior['identity']:
            started.append({'name':name,'starting':True,'pid':prior['pid']});continue
        with (directory/(name+'.stdout')).open('ab') as stdout,(directory/(name+'.stderr')).open('ab') as stderr:
            p=subprocess.Popen(commands[name],env=env,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
        time.sleep(.2)
        identity=process_identity(p.pid)
        if not identity:raise RuntimeError(name+' exited at startup; see research/state/services/'+name+'.stderr')
        atomic(directory/(name+'.json'),{'pid':p.pid,'identity':identity,'started_at':now(),'argv':commands[name]})
        started.append({'name':name,'pid':p.pid,'starting':True})
    return started
