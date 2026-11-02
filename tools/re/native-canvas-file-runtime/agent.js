'use strict';
let phase='setup';
rpc.exports={phase(value){phase=value;return phase;}};
function publish(value){send({...value,agent_phase:phase});}
const m=Process.getModuleByName('PreviewsXcode');
if(m.path!=='/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')throw Error('path mismatch');
function uuid(mod){if(mod.base.readU32()!==0xfeedfacf)throw Error('Mach header');let p=mod.base.add(32),value=null;for(let i=0,n=mod.base.add(16).readU32();i<n;i++){const c=p.readU32(),s=p.add(4).readU32();if(s<8)throw Error('load-command bound');if(c===0x1b)value=Array.from(new Uint8Array(p.add(8).readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join('');p=p.add(s);}return value;}
if(uuid(m)!=='25c99c664185307188e31ab474573a10')throw Error('UUID mismatch');
const startDepth=new Map(),stopDepth=new Map();
function listener(name,offset,depth){Interceptor.attach(m.base.add(offset),{onEnter(){this.t=Process.getCurrentThreadId();depth.set(this.t,(depth.get(this.t)||0)+1);publish({event:name,thread:this.t});},onLeave(){depth.set(this.t,depth.get(this.t)-1);}});}
listener('build-start-listener',0x16ed0c,startDepth);listener('build-stop-listener',0x16ef1c,stopDepth);
let nextInvocation=0;
const active=new Map();
Interceptor.attach(m.base.add(0x248ef0),{
 onEnter(){this.t=Process.getCurrentThreadId();this.previous=active.get(this.t);this.id=++nextInvocation;active.set(this.t,this.id);publish({event:'workspace-event-handler',thread:this.t,invocation:this.id});},
 onLeave(){publish({event:'workspace-event-handler-return',thread:this.t,invocation:this.id});if(this.previous===undefined)active.delete(this.t);else active.set(this.t,this.previous);}
});
// Original observation probes at previously qualified native basic-block entries.
for(const [name,offset] of [
 ['build-timestamp-written',0x2498c4],
 ['modified-timestamp-presence',0x2495e0],
 ['modified-time-check',0x249b8c],
 ['modified-time-pass',0x249bf4],
 ['modified-time-suppressed-cleanup',0x249e08],
 ['modified-scene-update',0x24a264]
]) Interceptor.attach(m.base.add(offset),{onEnter(){const t=Process.getCurrentThreadId();if(active.has(t))publish({event:name,thread:t,invocation:active.get(t)});}});
Interceptor.attach(m.base.add(0x24e3d4),{onEnter(){const t=Process.getCurrentThreadId();if(active.has(t))publish({event:'modified-file-filter',thread:t,invocation:active.get(t)});}});
const api=Process.getModuleByName('PreviewsIDEAPI');if(uuid(api)!=='b8c195f9db4837999653d7aa8bcb986e')throw Error('API UUID mismatch');
Interceptor.attach(api.base.add(0x8fb0),{onLeave(value){const t=Process.getCurrentThreadId();if(startDepth.get(t)>0)publish({event:'isPreviewsBuild',thread:t,value:value.toUInt32()&1});}});
const getClass=new NativeFunction(Module.getGlobalExportByName('objc_getClass'),'pointer',['pointer']);
const selector=new NativeFunction(Module.getGlobalExportByName('sel_registerName'),'pointer',['pointer']);
const getMethod=new NativeFunction(Module.getGlobalExportByName('class_getInstanceMethod'),'pointer',['pointer','pointer']);
const getImp=new NativeFunction(Module.getGlobalExportByName('method_getImplementation'),'pointer',['pointer']);
const op=getClass(Memory.allocUtf8String('IDEBuildOperation')),method=getMethod(op,selector(Memory.allocUtf8String('result')));if(method.isNull())throw Error('result selector missing');
Interceptor.attach(getImp(method),{onEnter(args){this.object=args[0].toString();},onLeave(value){const t=Process.getCurrentThreadId();if(stopDepth.get(t)>0)publish({event:'build-result-read',thread:t,value:value.toUInt32(),object:this.object});}});

for(const [name,offset] of [['should-update-file-result',0x250314],['is-open-thunkable-result',0x250a48]])
 Interceptor.attach(m.base.add(offset),{onEnter(){this.t=Process.getCurrentThreadId();this.invocation=active.get(this.t);},onLeave(value){if(this.invocation!==undefined)publish({event:name,thread:this.t,invocation:this.invocation,value:value.toUInt32()&1});}});
publish({event:'hooks-ready',uuid:uuid(m),api_uuid:uuid(api)});
