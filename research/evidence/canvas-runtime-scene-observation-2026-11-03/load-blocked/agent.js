'use strict';
const image=Process.getModuleByName('PreviewsScenes');
function uuid(m){let p=m.base.add(32),value=null;for(let i=0,n=m.base.add(16).readU32();i<n;i++){const c=p.readU32(),s=p.add(4).readU32();if(s<8)throw Error('load-command size');if(c===0x1b)value=Array.from(new Uint8Array(p.add(8).readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join('');p=p.add(s);}return value;}
if(uuid(image)!=='afaf513ac1153755840e1d82b40e7d93')throw Error('Scene UUID mismatch');
const library=Module.load(__WEAK_LIBRARY__);
const weakNew=new NativeFunction(library.getExportByName('canvas_weak_new'),'pointer',['pointer']);
const weakAlive=new NativeFunction(library.getExportByName('canvas_weak_alive'),'int',['pointer']);
const weakDispose=new NativeFunction(library.getExportByName('canvas_weak_dispose'),'void',['pointer']);
const className=new NativeFunction(Module.getGlobalExportByName('object_getClassName'),'pointer',['pointer']);
const isMain=new NativeFunction(Module.getGlobalExportByName('pthread_main_np'),'int',[]);
const dispatchMain=Module.getGlobalExportByName('_dispatch_main_q');
const dispatch=new NativeFunction(Module.getGlobalExportByName('dispatch_async_f'),'void',['pointer','pointer','pointer']);
const objects=[],addresses=new Map(),listeners=[],pending=[];let serial=0,closing=false;
listeners.push(Interceptor.attach(image.base.add(0x58e98),{onEnter(){if(closing||objects.length>=20)return;const p=this.context.x20,key=p.toString(),old=addresses.get(key);if(old&&!old.deallocated)return;if(isMain()!==1){send({event:'capture-skipped-not-main'});return;}const name=className(p).readUtf8String();if(!name.includes('EditorScene')){send({event:'class-guard-failed'});return;}const object={id:++serial,weak:weakNew(p),deallocated:false};objects.push(object);addresses.set(key,object);send({event:'editor-scene-observed',id:object.id,expected_class:true,main:true,weak_alive:weakAlive(object.weak)===1});}}));
for(const [event,offset] of [['deinitializing',0x5dcf8],['deallocating',0x5e078]])listeners.push(Interceptor.attach(image.base.add(offset),{onEnter(){this.object=addresses.get(this.context.x20.toString());if(this.object)send({event:event+'-enter',id:this.object.id,main:isMain()===1});},onLeave(){if(this.object){if(event==='deallocating')this.object.deallocated=true;send({event:event+'-return',id:this.object.id,main:isMain()===1});}}}));
const mainCallback=new NativeCallback(function(){const request=pending.shift();if(!request)return;if(isMain()!==1){send({event:'main-queue-guard-failed',label:request.label});return;}if(request.cleanup){for(const object of objects)weakDispose(object.weak);send({event:'cleanup-done',label:request.label,weak_boxes_disposed:objects.length,explicit_module_unload_attempted:false});return;}send({event:'snapshot',label:request.label,main:true,objects:objects.map(o=>({id:o.id,weak_alive:weakAlive(o.weak)===1,deallocating_destructor_return_seen:o.deallocated}))});},'void',['pointer']);
function receive(){recv('command',message=>{const r=message.payload;if(r.cleanup){closing=true;for(const listener of listeners)listener.detach();}pending.push(r);dispatch(dispatchMain,NULL,mainCallback);receive();});}receive();
send({event:'hooks-ready',uuid:uuid(image),weak_library_loaded:true,tracked_class:'EditorScene',max_objects:20,weak_poll_main_queue:true});
