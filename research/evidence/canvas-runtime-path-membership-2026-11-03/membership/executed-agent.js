'use strict';
function uuid(m){let p=m.base.add(32),v=null;for(let i=0,n=m.base.add(16).readU32();i<n;i++){const c=p.readU32(),s=p.add(4).readU32();if(s<8)throw Error('load command');if(c===0x1b)v=Array.from(new Uint8Array(p.add(8).readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join('');p=p.add(s);}return v;}
const x=Process.getModuleByName('PreviewsXcode'),s=Process.getModuleByName('PreviewsScenes');
if(uuid(x)!=='25c99c664185307188e31ab474573a10'||uuid(s)!=='afaf513ac1153755840e1d82b40e7d93')throw Error('image mismatch');
let phase='baseline',serial=0,total=0;const active=new Map(),listeners=[],removedIds=new Set(),filterActive=new Map();
const trackEmpty = false;
function emit(v){if(total++<1000)send({...v,phase});}
listeners.push(Interceptor.attach(x.base.add(0x248ef0),{onEnter(){this.t=Process.getCurrentThreadId();this.old=active.get(this.t);this.id=++serial;active.set(this.t,this.id);emit({event:'workspace-handler-enter',id:this.id,thread:this.t});},onLeave(){emit({event:'workspace-handler-return',id:this.id,thread:this.t});removedIds.delete(this.id);if(this.old===undefined)active.delete(this.t);else active.set(this.t,this.old);}}));
listeners.push(Interceptor.attach(x.base.add(0x2499c4),{onEnter(){const t=Process.getCurrentThreadId();if(active.has(t)){removedIds.add(active.get(t));emit({event:'removed-files-block',id:active.get(t),thread:t});}}}));
// Scoped interior instruction observations, never function-return probes.
listeners.push(Interceptor.attach(x.base.add(0x249a1c),{onEnter(){const t=Process.getCurrentThreadId(),id=active.get(t);if(removedIds.has(id))emit({event:'removed-filter-count-branch',id,thread:t,count_register:this.context.x21.toString()});}}));
if(trackEmpty)listeners.push(Interceptor.attach(x.base.add(0x249dfc),{onEnter(){const t=Process.getCurrentThreadId(),id=active.get(t);if(removedIds.has(id))emit({event:'removed-empty-cleanup-block',id,thread:t});}}));
function watch(name,address,owner){listeners.push(Interceptor.attach(address,{onEnter(){this.t=Process.getCurrentThreadId();this.id=active.get(this.t);this.record=this.id!==undefined;if(this.record&&name==='removed-filter'){this.oldFilter=filterActive.get(this.t);filterActive.set(this.t,this.id);}if(this.record)emit({event:name+'-enter',id:this.id,thread:this.t,caller_image:Process.findModuleByAddress(this.returnAddress)?.name??null,caller_offset:Process.findModuleByAddress(this.returnAddress)?this.returnAddress.sub(Process.findModuleByAddress(this.returnAddress).base).toString():null});},onLeave(){if(this.record)emit({event:name+'-return',id:this.id,thread:this.t});if(this.record&&name==='removed-filter'){if(this.oldFilter===undefined)filterActive.delete(this.t);else filterActive.set(this.t,this.oldFilter);}}}));}
watch('removed-filter',x.base.add(0x24e3d4),'PreviewsXcode');
watch('workspace-removed',s.getExportByName('$s14PreviewsScenes14WorkspaceSceneC6update23forRemovedFileLocationsySay8LocationQzG_tF'),'PreviewsXcode');
watch('editor-removed',s.base.add(0x579fc),'PreviewsScenes');
watch('coalescer',x.base.add(0x4f43c),'PreviewsXcode');
watch('scene-update',s.getExportByName('$s14PreviewsScenes14WorkspaceSceneC14setNeedsUpdate3fory0A8Pipeline07PreviewG6ReasonV_tF'),'PreviewsXcode');
const expectedPaths = {"primary": "/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/PreviewLab.swift", "auxiliary": "/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/RuntimeRefreshDependency.swift", "project": "/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/PreviewLab.xcodeproj/project.pbxproj"};
const objcSend=Module.getGlobalExportByName('objc_msgSend');
const sendPointer=new NativeFunction(objcSend,'pointer',['pointer','pointer']);
const responds=new NativeFunction(objcSend,'uint8',['pointer','pointer','pointer']);
const selector=new NativeFunction(Module.getGlobalExportByName('sel_registerName'),'pointer',['pointer']);
const className=new NativeFunction(Module.getGlobalExportByName('object_getClassName'),'pointer',['pointer']);
const mainThread=new NativeFunction(Module.getGlobalExportByName('pthread_main_np'),'int',[]);
const sel={};for(const n of ['respondsToSelector:','fileURL','path','UTF8String'])sel[n]=selector(Memory.allocUtf8String(n));
function pathIdentity(p){const result={path_kind:'unavailable',getter_main:mainThread()===1,getter_receiver_expected_family:false,getter_read_available:false};if(!result.getter_main||p.isNull())return result;result.getter_receiver_expected_family=className(p).readUtf8String().includes('DVTFilePath');if(!result.getter_receiver_expected_family)return result;
 let object=p;for(const name of ['fileURL','path','UTF8String']){if(responds(object,sel['respondsToSelector:'],sel[name])===0)return result;object=sendPointer(object,sel[name]);if(object.isNull())return result;}
 const value=object.readUtf8String();result.getter_read_available=true;result.path_kind=Object.keys(expectedPaths).find(k=>expectedPaths[k]===value)??'other';return result;}
for(const [event,offset,reg] of [['filter-input-count',0x24e438,'x9'],['filter-candidate-count',0x24e6bc,'x21']])listeners.push(Interceptor.attach(x.base.add(offset),{onEnter(){const t=Process.getCurrentThreadId(),id=filterActive.get(t);if(id!==undefined)emit({event,id,thread:t,count_register:this.context[reg].toString()});}}));
listeners.push(Interceptor.attach(x.base.add(0x24e4d0),{onEnter(){const t=Process.getCurrentThreadId(),id=filterActive.get(t);if(id!==undefined)emit({event:'filter-optional-type',id,thread:t,present:!this.context.x23.isNull(),...pathIdentity(this.context.x0)});}}));
for(const [event,offset] of [['filter-predicate-result',0x250314],['filter-thunkable-result',0x250a48]])listeners.push(Interceptor.attach(x.base.add(offset),{onEnter(){this.t=Process.getCurrentThreadId();this.id=filterActive.get(this.t);},onLeave(v){if(this.id!==undefined)emit({event,id:this.id,thread:this.t,value:v.toUInt32()&1});}}));
function receive(){recv('command',m=>{phase=m.payload.label;if(m.payload.cleanup)for(const l of listeners)l.detach();send({event:m.payload.cleanup?'cleanup-done':'phase-ack',label:phase,total_events:total});receive();});}receive();
send({event:'hooks-ready',xcode_uuid:uuid(x),scenes_uuid:uuid(s),max_events:1000,path_identity_getters:true,filter_input_probes:true,filter_count_probe:true,empty_cleanup_probe:trackEmpty});
