#!/usr/bin/env python3
"""Fixed experiment adapters. Runs only reviewed local tool entry points."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.core import ROOT, PROJECT_ROOT, atomic, digest, load


def command(argv,out,name,timeout=600):
    with (out/(name+'.stdout')).open('wb') as stdout, (out/(name+'.stderr')).open('wb') as stderr:
        result=subprocess.run([str(v) for v in argv],cwd=str(ROOT),stdout=stdout,stderr=stderr,timeout=timeout)
    if result.returncode: raise RuntimeError(name+' exited '+str(result.returncode))


def ghidra_config():
    config=load(PROJECT_ROOT/'research/local-config.json',{})
    home=config.get('ghidra_home')
    if not home:
        candidate=pathlib.Path.home()/'GhidraVibe/result-ghidra-vibe-fresh/lib/ghidra'
        if candidate.is_dir(): home=str(candidate.resolve())
    java=config.get('java_home')
    if not java:
        candidates=list(pathlib.Path('/nix/store').glob('*-semeru-bin-21*/Library/Java/JavaVirtualMachines/*/Contents/Home')) if pathlib.Path('/nix/store').exists() else []
        if candidates: java=str(sorted(candidates)[0])
    return home,java,config


def perform(kind,out,p):
    xcode=p.get('xcode','/Applications/Xcode.app')
    image=p.get('binary',xcode+'/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost')
    if kind=='linux_wasm':
        from reloop.linuxwasm import corpus
        return corpus(out)
    if kind=='rea_native':
        from reloop.rea import run
        return run(out,p.get('binary',xcode+'/Contents/SharedFrameworks/PreviewsFoundationHost.framework/PreviewsFoundationHost'),p.get('owned_control',False))
    if kind=='inventory':
        command([sys.executable,ROOT/'tools/re/collect.py','--xcode',xcode,'--out',out/'inventory'],out,'collect')
        d=load(out/'inventory/inventory.json')
        return {'binaries':sum(t['exists'] for t in d['targets']),
                'failed_commands':sum(c['exit_code']!=0 for t in d['targets'] for c in t.get('commands',[])),
                'sdk_stubs':len(list((out/'inventory').glob('*.tbd.txt')))}
    if kind=='runtime':
        env=os.environ.copy();env['RE_OUT']=str(out);env['XCODE_APP']=xcode
        with (out/'runtime.stdout').open('wb') as stdout,(out/'runtime.stderr').open('wb') as stderr:
            r=subprocess.run(['sh',str(ROOT/'tools/re/dump-runtime.sh')],env=env,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=240)
        if r.returncode: raise RuntimeError('runtime helpers failed')
        probe=load(out/'runtime/plist-probe.json');keys=load(out/'runtime/message-keys.json')
        import plistlib,base64
        fixture=plistlib.loads(base64.b64decode(probe['base64']))
        datasets={n:load(out/('runtime/'+n+'.json')) for n in ['os','host']}
        return {'all_loaded':all(l['loaded'] for d in datasets.values() for l in d['loads']),
                'uv_round_trip':bool(probe['uv_round_trip_equal']), 'foundation_round_trip':bool(probe['foundation_round_trip_equal']),
                'independent_python_decode':fixture['type']=='synthetic-probe' and fixture['bytes']==b'hello',
                'message_keys':keys,'images':{n:d['images'] for n,d in datasets.items()}}
    if kind=='disassembly':
        args=[sys.executable,ROOT/'tools/re/disassemble.py','--binary',image,'--out',out/'disassembly',
              '--query',p.get('query','^$' if p.get('ranges') else 'MessageTypeKey.getter|OneWayMessageKey.getter')]
        for value in p.get('ranges',[]):args+=['--range',value]
        command(args,out,'disassemble')
        files=list((out/'disassembly').glob('*.txt'));facts={}
        if p.get('guard_control',False):
            if len(files)!=1:raise ValueError('Guard control requires one selected closure')
            from reloop.continuation import inspect as inspect_guard
            facts=inspect_guard(files[0].read_text());atomic(out/'continuation-guard.json',facts)
        if p.get('default_control',False):
            if len(files)!=1:raise ValueError('Default control requires one selected getter')
            from reloop.continuation import inspect_default
            from reloop.swiftmeta import MachO
            facts.update(inspect_default(files[0].read_text(),MachO(image)))
            atomic(out/'continuation-default.json',facts)
        if p.get('cancel_control',False):
            if len(files)!=1:raise ValueError('Cancellation control requires one selected entry')
            from reloop.continuation import inspect_cancel
            facts.update(inspect_cancel(files[0].read_text()))
            atomic(out/'cancellation-guard.json',facts)
        if p.get('deinit_control',False):
            if len(files)!=1:raise ValueError('Deinit control requires one selected entry')
            from reloop.continuation import inspect_deinit
            facts.update(inspect_deinit(files[0].read_text()))
            atomic(out/'deinit-guard.json',facts)
        if p.get('callback_control',False):
            from reloop.continuation import inspect_callbacks
            facts.update(inspect_callbacks([f.read_text() for f in files]))
            atomic(out/'callback-boundaries.json',facts)
        if p.get('isolation_control',False):
            if len(files)!=1:raise ValueError('Isolation control requires one helper')
            from reloop.continuation import inspect_isolation
            facts.update(inspect_isolation(files[0].read_text()))
            atomic(out/'isolation-boundary.json',facts)
        if p.get('invalidation_control',False):
            from reloop.continuation import inspect_invalidation
            facts.update(inspect_invalidation([f.read_text() for f in files]))
            atomic(out/'invalidation-boundaries.json',facts)
        if p.get('dictionary_control',False):
            from reloop.observerremoval import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'observer-removal.json',facts)
        if p.get('token_link_control',False):
            from reloop.tokenlink import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'token-link.json',facts)
        if p.get('cleanup_control',False):
            from reloop.tokenconsume import inspect
            from reloop.swiftmeta import MachO
            from reloop.stubbind import inspect as inspect_stub
            if len(files)!=2:raise ValueError('Cleanup control requires consumer and import stub ranges')
            bodies={int(f.stem,16):f.read_text() for f in files}
            if set(bodies)!={0x42648,0x1311c8}:raise ValueError('Exact cleanup/stub entries required')
            native_image=MachO(image)
            facts.update(inspect(bodies[0x42648],native_image))
            binding=inspect_stub(bodies[0x1311c8],native_image,0x1311c8,'_swift_bridgeObjectRelease','/usr/lib/swift/libswiftCore.dylib')
            facts['release_binding_scope']=binding.pop('scope')
            facts.update(binding)
            atomic(out/'token-consume.json',facts)
        if p.get('witness_control',False):
            from reloop.tokenwitness import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'token-witness.json',facts)
        if p.get('descriptor_control',False):
            from reloop.tokendescriptor import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'token-descriptor.json',facts)
        if p.get('pattern_control',False):
            from reloop.statepattern import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'state-pattern.json',facts)
        if p.get('ownership_control',False):
            from reloop.storageownership import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'storage-ownership.json',facts)
        if p.get('tag_control',False):
            from reloop.statetag import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'state-tag.json',facts)
        if p.get('result_control',False):
            from reloop.resulttag import inspect
            from reloop.swiftmeta import MachO
            facts.update(inspect([f.read_text() for f in files],MachO(image)))
            atomic(out/'result-tag.json',facts)
        selections=load(out/'disassembly/selection.json')
        return {'function_count':len(files),'entry_body_count':sum(s['entry_instruction'] for s in selections),
                'address_fallback_count':sum(s['mode']=='bounded-address' for s in selections),'image_sha256':digest(image),**facts}
    if kind=='ghidra':
        home,java,config=ghidra_config()
        if not home or not java: raise RuntimeError('Ghidra/JDK unavailable; see doctor and local-config.example.json')
        projects=out/'projects';projects.mkdir()
        addresses=p.get('addresses',['9661c','96600'])
        target=out/'decompiled.txt'
        args=[str(pathlib.Path(java)/'bin/java'),'-Xmx2G','-Djava.awt.headless=true',
              '-Djava.system.class.loader=ghidra.GhidraClassLoader','-Duser.country=US','-Duser.language=en',
              '-Dapplication.settingsdir='+str(out/'settings'),'-Djava.io.tmpdir='+str(out/'tmp'),
              '-cp',str(pathlib.Path(home)/'Ghidra/Framework/Utility/lib/Utility.jar'),
              'ghidra.Ghidra','ghidra.app.util.headless.AnalyzeHeadless',str(projects),'PreviewResearch',
              '-import',image,'-max-cpu','2','-analysisTimeoutPerFile','120','-scriptPath',str(ROOT/'tools/re'),
              '-postScript','DumpPreviewFunctions.java',str(target)]+addresses
        (out/'tmp').mkdir()
        atomic(out/'command.json',args)
        command(args,out,'ghidra',timeout=600)
        text=target.read_text();log=(out/'ghidra.stdout').read_text(errors='replace')+(out/'ghidra.stderr').read_text(errors='replace')
        return {'decompiled_functions':text.count('\nAddress:'),'failed_functions':text.count('FAILED:')+text.count('NO FUNCTION'),
                'partial_analysis':'Analysis timed out' in log,'project_saved':'Save succeeded' in log,'image_sha256':digest(image)}
    if kind=='ghidra_mcp':
        from reloop.ghidra import call
        return call(p.get('tool','vibe_health'),p.get('arguments',{}),out)
    if kind=='connected_probe':
        from reloop.connected import connected
        return connected(out)
    if kind=='plist_corpus':
        if p.get('decode_control',False):
            from reloop.plistdecode import corpus as decode_corpus
            return decode_corpus(out)
        from reloop.corpus import corpus
        return corpus(out,p.get('seed',1),p.get('cases',24))
    if kind=='swift_metadata':
        from reloop.swiftmeta import inspect
        data=inspect(image,p.get('maximum',1000));atomic(out/'swift-metadata.json',data)
        atomic(out/'swift-index.json',{'image_sha256':data['image_sha256'],'types':[{'name':t.get('name'),'kind':t['kind'],'address':t['address'],'fields':[f.get('name') for f in t.get('fields',[])]} for t in data['types']]})
        facts={}
        if p.get('state_control',False):
            from reloop.continuation import inspect_state_metadata
            facts=inspect_state_metadata(data);atomic(out/'fulfillment-state.json',facts)
        return {'type_count':len(data['types']),'field_count':sum(len(t.get('fields',[])) for t in data['types']),'parse_errors':len(data['errors']),'image_sha256':data['image_sha256'],**facts}
    if kind=='xcode_preview':
        from reloop.canvas import capture
        return capture(out,p.get('variants',[0,1]),p.get('trace',False),p.get('scheme_control',False))
    if kind in {'xpc_corpus','xpc_negative','xpc_prefix'}:
        from reloop.xpc import corpus,negatives,prefixes
        if kind=='xpc_corpus':return corpus(out,p.get('seed',9),p.get('cases',32))
        return negatives(out) if kind=='xpc_negative' else prefixes(out)
    if kind=='agent_discriminants':
        from reloop.discriminants import recover
        return recover(out)
    if kind=='raw_coder':
        from reloop.rawcoder import matrix
        return matrix(out)
    if kind=='surface_corpus' and p.get('gpu_control',False):
        from reloop.surfacegpu import corpus
        return corpus(out)
    if kind=='surface_corpus':
        from reloop.surface import corpus
        return corpus(out)
    if kind=='surface_ipc' and p.get('gpu_control',False):
        if p.get('exit_order')!='receiver':raise ValueError('GPU handoff requires reviewed receiver-first mode')
        from reloop.surfacegpuipc import corpus
        return corpus(out,p.get('gpu_consumer_control',False),p.get('gpu_stall_control',False),p.get('gpu_reuse_control',False))
    if kind=='surface_ipc':
        from reloop.surfaceipc import corpus
        return corpus(out,p.get('exit_order','sender'))
    if kind=='surface_failure':
        if p.get('control')=='late_ack':
            from reloop.surfacelate import corpus
            return corpus(out)
        from reloop.surfacefailure import corpus,use_corpus
        return use_corpus(out) if p.get('control','faults')=='use_state' else corpus(out)
    if kind=='portable_solid':
        if p.get('source_control',False):
            from reloop.viewsource import corpus
            return corpus(out,p.get('second_runtime',False))
        from reloop.portable import corpus
        return corpus(out,p.get('second_runtime',False))
    if kind=='surface_payload':
        from reloop.surfacepayload import recover
        return recover(out,p.get('payload','IOSurfacePayload'))
    if kind=='surface_reuse':
        from reloop.surfacereuse import corpus
        return corpus(out)
    if kind=='xcode_bridge_probe':
        from reloop.bridgeprobe import probe
        return probe(out,p.get('managed',False))
    if kind=='native_reference' and p.get('solid_control',False):
        from reloop.reference import solid_corpus
        return solid_corpus(out)
    if kind=='native_reference' and p.get('repeat_control',False):
        from reloop.reference import corpus
        return corpus(out)
    if kind in {'lldb_smoke','frida_smoke','native_reference','preview_hook_smoke'}:
        from reloop.trace import smoke
        return smoke(kind,out)
    raise ValueError('unknown adapter')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('adapter');parser.add_argument('--out',type=pathlib.Path,required=True);parser.add_argument('--params',default='{}')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    try:
        result=perform(args.adapter,args.out,json.loads(args.params))
        atomic(args.out/'result.json',{'observations':result})
        print(json.dumps(result));return 0
    except Exception as error:
        atomic(args.out/'result.json',{'error':str(error),'error_type':type(error).__name__,'observations':{}})
        print(str(error),file=sys.stderr);return 1

if __name__=='__main__': raise SystemExit(main())
