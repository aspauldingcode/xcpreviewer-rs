"""Pinned, bounded REA observer-removal pilot; native results stay local."""
import json
import os
import pathlib
import re
import struct
import subprocess
import time
from reloop.core import ROOT, PROJECT_ROOT, atomic, canonical_hash, digest, load
from reloop.mcp_client import Client
from reloop.swiftmeta import MachO

VERSION='6.2.0'
IMAGE_SHA='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
CALLS={0x42604:(0x42634,0xedf78),0x428d0:(0x428e8,0xee75c)}


def runtime_identity(package):
    package=pathlib.Path(package)
    files={str(p.relative_to(package)):digest(p) for p in sorted(package.rglob('*'))
           if p.is_file() and p.suffix in {'.js','.mjs','.java','.json'} and 'node_modules' not in p.relative_to(package).parts}
    return {'code_files':len(files),'code_sha256':canonical_hash(files)}


def envelope(response):
    if response.get('isError'):
        raise RuntimeError('REA tool failed; retained response contains provider diagnostics')
    value=response.get('structuredContent')
    if not isinstance(value,dict):raise ValueError('Missing REA structured response')
    return value


def evidence(response,image_hash,operation):
    value=envelope(response)
    if value.get('subject',{}).get('digest',{}).get('sha256')!=image_hash:raise ValueError('REA image identity mismatch')
    if value.get('subject',{}).get('architecture')!='arm64':raise ValueError('REA architecture mismatch')
    if value.get('provider',{}).get('id')!='ghidra':raise ValueError('REA provider mismatch')
    if value.get('operation')!=operation:raise ValueError('REA operation mismatch')
    if not re.fullmatch(r'ev_[a-f0-9]{64}',value.get('evidence_id','')):raise ValueError('Invalid REA evidence ID')
    profile=value.get('analysis_profile')
    if not isinstance(profile,dict) or not re.fullmatch('[a-f0-9]{64}',profile.get('digest','')):raise ValueError('Missing REA analysis profile')
    return value


def address(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{1,16}',value):raise ValueError('Invalid REA address')
    return int(value,16)


def verify_pair(function,instruction,image,entry,site,target,image_hash):
    f=evidence(function,image_hash,'analyze_function');i=evidence(instruction,image_hash,'inspect_native_instruction')
    if f['analysis_profile']['digest']!=i['analysis_profile']['digest']:raise ValueError('REA profile changed')
    body=f['normalized_result'];ins=i['normalized_result']
    if address(body['procedure']['address'])!=entry:raise ValueError('REA entry mismatch')
    if not body.get('pseudocode') or not body.get('assembly'):raise ValueError('Missing native function output')
    refs=body.get('outgoing_references',[])
    if not any(address(r['source_address'])==site and address(r['target_address'])==target and r.get('kind',{}).get('call') is True for r in refs):raise ValueError('Missing expected native call reference')
    if address(ins['address'])!=site or ins['status']!='decoded' or ins['architecture'] not in {'arm64','AARCH64:LE:64:AppleSilicon'} or ins['length']!=4:raise ValueError('Invalid native instruction')
    raw=bytes.fromhex(ins['bytes']);offset=image.file_offset(site)
    if len(raw)!=4 or raw!=image.data[offset:offset+4]:raise ValueError('Instruction bytes mismatch')
    word=struct.unpack('<I',raw)[0];imm=word&0x3ffffff
    if imm&0x2000000:imm-=0x4000000
    if word&0xfc000000!=0x94000000 or site+imm*4!=target:raise ValueError('Encoded BL target mismatch')
    flow=ins['flow']
    if flow['kind']!='call' or flow['computed'] or flow['conditional'] or target not in [address(v) for v in flow['direct_destinations']]:raise ValueError('REA flow disagrees with encoded BL')
    return {'entry':hex(entry),'call_site':hex(site),'target':hex(target),'compared_bytes':4,'function_evidence_id':f['evidence_id'],'instruction_evidence_id':i['evidence_id'],'profile_digest':f['analysis_profile']['digest'],'provider_version':f['provider']['version']}


def owned_target(out):
    target=out/'rea-owned-probe'
    subprocess.run(['xcrun','clang','-arch','arm64','-O0',str(ROOT/'tools/re/rea/probe.c'),'-o',str(target)],check=True,capture_output=True,timeout=30)
    symbols=subprocess.run(['xcrun','nm','-n',str(target)],check=True,capture_output=True,text=True,timeout=15).stdout
    found={}
    for line in symbols.splitlines():
        fields=line.split()
        if len(fields)==3 and fields[2] in {'_reloop_rea_entry','_reloop_rea_leaf'}:found[fields[2]]=int(fields[0],16)
    if set(found)!={'_reloop_rea_entry','_reloop_rea_leaf'}:raise ValueError('Owned probe symbols missing')
    entry=found['_reloop_rea_entry'];target_address=found['_reloop_rea_leaf'];image=MachO(target);calls=[]
    for site in range(entry,entry+128,4):
        word=image.u32(image.file_offset(site))
        if word&0xfc000000==0x94000000:
            imm=word&0x3ffffff
            if imm&0x2000000:imm-=0x4000000
            if site+imm*4==target_address:calls.append(site)
        if word==0xd65f03c0:break
    if len(calls)!=1:raise ValueError('Owned probe requires one independently decoded leaf call')
    atomic(out/'owned-target.json',{'source_sha256':digest(ROOT/'tools/re/rea/probe.c'),'symbols':found,'call_site':hex(calls[0])})
    return str(target.resolve()),{entry:(calls[0],target_address)}


def run(out,image_path,owned_control=False):
    from reloop.worker import ghidra_config
    calls=CALLS
    if owned_control:image_path,calls=owned_target(out)
    image=MachO(image_path);sha=digest(image_path)
    if not owned_control and sha!=IMAGE_SHA:raise ValueError('Reviewed REA pilot requires pinned FoundationHost image')
    install=PROJECT_ROOT/'research/build/rea'
    package=install/'node_modules/rea-agents';entry=package/'scripts/rea.mjs'
    if load(package/'package.json',{}).get('version')!=VERSION:raise RuntimeError('Run tools/re/bootstrap-rea.sh for pinned REA')
    if digest(ROOT/'tools/re/rea/package-lock.json')!=digest(install/'package-lock.json'):raise ValueError('Installed REA lock mismatch')
    home,java,_=ghidra_config()
    if not home or not java:raise RuntimeError('Ghidra/JDK unavailable')
    env=dict(os.environ,GHIDRA_INSTALL_DIR=home,JAVA_HOME=java,REA_ANALYSIS_PROVIDER='ghidra',REA_GHIDRA_STARTUP_TIMEOUT_MS='90000' if owned_control else '330000')
    facts={'rea_version':VERSION,'rea_entry_sha256':digest(entry),'rea_runtime':runtime_identity(package),'image_sha256':sha,'claim_scope':'static native discovery; selected encoded BL instructions only','owned_control':owned_control}
    started=time.monotonic();results=[]
    with (out/'rea.stderr').open('w') as err:
        c=Client(['node',str(entry),'mcp'],err,timeout=110 if owned_control else 350,env=env)
        try:
            listing=c.request('tools/list',{});atomic(out/'rea-tools.json',listing)
            names={t['name'] for t in listing['tools']}
            required={'open_binary','analyze_function','inspect_native_instruction','close_binary'}
            if not required<=names:raise ValueError('Required REA tools missing')
            facts['discovered_tools']=len(names)
            def call(name,args,label):
                t=time.monotonic();response=c.request('tools/call',{'name':name,'arguments':args})
                atomic(out/(label+'.json'),response);atomic(out/(label+'-timing.json'),{'seconds':round(time.monotonic()-t,3)})
                return response
            opened=envelope(call('open_binary',{'path':str(pathlib.Path(image_path).resolve()),'provider_id':'ghidra'},'open'))['result']
            if opened['sha256']!=sha or opened['architecture']!='arm64':raise ValueError('REA open identity mismatch')
            for fn,(site,target) in calls.items():
                f=call('analyze_function',{'procedure':hex(fn)},'function-'+format(fn,'x'))
                # Fail immediately on provider errors; do not repeat unchanged failures.
                evidence(f,sha,'analyze_function')
                i=call('inspect_native_instruction',{'address':hex(site)},'instruction-'+format(site,'x'))
                results.append(verify_pair(f,i,image,fn,site,target,sha))
        finally:
            try:
                closed=c.request('tools/call',{'name':'close_binary','arguments':{}});atomic(out/'close.json',closed)
                if envelope(closed).get('result','missing') is not None:raise ValueError('Unexpected REA cleanup response')
                facts['provider_closed']=True
            finally:c.close()
    facts.update({'native_functions':len(results),'encoded_call_targets_verified':len(results),'compared_bytes':sum(r['compared_bytes'] for r in results),'duration_seconds':round(time.monotonic()-started,3),'rea_verified':len(results)==len(calls)})
    atomic(out/'rea-verification.json',{'facts':facts,'functions':results});return facts
