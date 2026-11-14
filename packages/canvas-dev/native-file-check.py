#!/usr/bin/env python3
"""Actual public SwiftUI captures after real disposable file changes; no user project writes."""
from pathlib import Path
import argparse,json,os,plistlib,tempfile,time
from server import Session,sha
from project import resolve_source


def run(project_binding=False):
    deadline=time.monotonic()+180;trace=[];children={}
    with tempfile.TemporaryDirectory(prefix='canvas-native-file-') as directory:
        base=Path(directory);root=base/'Sources' if project_binding else base;root.mkdir(exist_ok=True)
        primary=root/'View.swift';extra=root/'Color.swift'
        source='import SwiftUI\n@MainActor func makePreview() -> some View { fixtureColor() }\n'
        colors={name:'import SwiftUI\n@MainActor func fixtureColor() -> Color { Color(.sRGB, red: '+r+', green: '+g+', blue: '+b+', opacity: 1) }\n' for name,r,g,b in [('blue','0','0','1'),('green','0','1','0')]}
        primary.write_text(source);extra.write_text(colors['blue'])
        metadata=None;extras=[extra]
        if project_binding:
            project=base/'Fixture.xcodeproj';project.mkdir()
            (project/'project.xcproj').write_text(json.dumps({'targets':[{'name':'Fixture'}],'files':[{'kind':'folder','path':'Sources','target-membership':['Fixture']}]}))
            primary,extras,metadata=resolve_source(project,'makePreview')
        session=Session(primary,base/'work',factory='makePreview',extra_sources=extras,project=metadata,width=64,height=64)
        session.configure({'chrome':False});session.start()
        def wait(predicate):
            end=min(deadline,time.monotonic()+45)
            while time.monotonic()<end:
                state=session.snapshot()
                with session.lock:
                    if session.child is not None:children[session.child.pid]=session.child
                if predicate(state):return state
                time.sleep(.05)
            raise AssertionError('Bounded native file campaign did not reach expected state: '+str(session.snapshot()['error']))
        def accept(name,revision,expected):
            before=time.monotonic();state=wait(lambda s:s['revision']>=revision and s['state']=='ready')
            with session.lock:data=session.blobs[state['frame']['sha256']]
            bitmap=plistlib.loads(data)['bitmapDescription'];pixels=bitmap['data'];bgra=bytes([expected[2],expected[1],expected[0],255])
            assert(bitmap['width'],bitmap['height'])==(128,128)
            assert pixels==bgra*(128*128),'Entire native bitmap differs from expected uniform color'
            entry=dict(stage=name,revision=state['revision'],source_sha256=state['frame']['source_sha256'],artifact_sha256=sha(data),pixel_sha256=sha(pixels),rgba=expected+[255],pixel_size=[128,128],wait_ms=round((time.monotonic()-before)*1000))
            trace.append(entry);return state
        def replace(path,text):
            temporary=path.with_suffix('.pending');temporary.write_text(text);os.replace(temporary,path)
        try:
            baseline=accept('initial blue from extra file',1,[0,0,255])
            replace(extra,colors['green']);green=accept('real atomic extra-file replacement',2,[0,255,0])
            assert baseline['frame']['source_sha256']==green['frame']['source_sha256'],'Primary source unexpectedly changed'
            replace(extra,'import SwiftUI\n@MainActor func fixtureColor() -> Color { MissingPreviewType() }\n')
            failed=wait(lambda s:s['state']=='error');assert failed['revision']==2 and failed['frame']==green['frame']
            trace.append(dict(stage='extra-file compile rejection',last_good_frame_retained=True,diagnostic_contains_missing_type='MissingPreviewType' in failed['error']))
            assert trace[-1]['diagnostic_contains_missing_type'],failed['error']
            replace(extra,colors['blue']);accept('extra-file recovery',3,[0,0,255])
            adaptive='import SwiftUI\nstruct Adaptive: View { @Environment(\\.colorScheme) var scheme; var body: some View { scheme == .dark ? Color.black : Color.white } }\n@MainActor func makePreview() -> some View { Adaptive() }\n'
            replace(primary,adaptive);accept('real primary-file replacement, light environment',4,[255,255,255])
            session.configure({'appearance':'dark','color_scheme':'dark'});accept('dark environment reaches actual View',5,[0,0,0])
            if project_binding:
                added=root/'NewColor.swift'
                fresh='import SwiftUI\n@MainActor func freshColor() -> Color { Color(.sRGB, red: 0, green: 1, blue: 0, opacity: 1) }\n'
                replace(added,fresh);replace(primary,source.replace('fixtureColor','freshColor'))
                newest=accept('new source automatically discovered in target folder',6,[0,255,0])
                added.unlink();failed=wait(lambda s:s['state']=='error')
                assert failed['revision']==6 and failed['frame']==newest['frame']
                assert 'freshColor' in failed['error']
                trace.append(dict(stage='removed new source rejects build',last_good_frame_retained=True))
                replace(added,fresh);accept('recreated source automatically recovers',7,[0,255,0])
            result=dict(classification='native public ImageRenderer; real disposable filesystem edits; no browser, simulator or Xcode-private lifecycle',trace=trace,compiler_version=session.snapshot()['frame']['compiler_version'],primary_input_preserved_during_extra_edits=True,project_binding=project_binding)
        finally:session.close()
        assert not session.thread.is_alive();assert session.child is None or session.child.poll() is not None
        assert children and all(child.poll() is not None for child in children.values())
        result['observed_top_level_builders_reaped']=len(children)
        result['watcher_joined']=True
        return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--project',action='store_true');args=parser.parse_args();result=run(args.project);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
