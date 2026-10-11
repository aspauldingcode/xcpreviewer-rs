// Only loaded into the owned trace fixture. Uses C ObjC-runtime APIs directly,
// so frida-objc-bridge is not required by Frida 17's bare create_script API.
'use strict';
const hooks = [];
let sequence = 0;
function emit(kind, value) { send(Object.assign({kind, sequence: ++sequence, pid: Process.id, thread: Process.getCurrentThreadId(), timestamp_ms: Date.now()}, value)); }
function imageIdentity(m) {
  const result = {name:m.name,path:m.path,base:m.base.toString(),size:m.size,uuid:null};
  try {
    const magic=m.base.readU32();
    if (magic !== 0xfeedfacf) return result;
    const count=m.base.add(16).readU32();let cursor=m.base.add(32);
    for (let i=0;i<count && i<1024;i++) {
      const command=cursor.readU32(), size=cursor.add(4).readU32();
      if (size<8) break;
      if (command===0x1b) {
        const bytes=new Uint8Array(cursor.add(8).readByteArray(16));
        result.uuid=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');break;
      }
      cursor=cursor.add(size);
    }
  } catch (e) { result.identity_error=String(e); }
  return result;
}
const fixture=Process.mainModule;
const tick=fixture.findExportByName('preview_probe_tick');
if (tick===null) throw new Error('owned fixture tick export missing');
hooks.push(Interceptor.attach(tick, {
  onEnter(args) { installObjCHook(); this.input=args[0].toInt32(); },
  onLeave(retval) { emit('tick',{input:this.input,output:retval.toInt32(),image:imageIdentity(fixture),offset:tick.sub(fixture.base).toString()}); }
}));
const objcGetClass=new NativeFunction(Module.getGlobalExportByName('objc_getClass'),'pointer',['pointer']);
const selRegister=new NativeFunction(Module.getGlobalExportByName('sel_registerName'),'pointer',['pointer']);
const getMethod=new NativeFunction(Module.getGlobalExportByName('class_getInstanceMethod'),'pointer',['pointer','pointer']);
const getImp=new NativeFunction(Module.getGlobalExportByName('method_getImplementation'),'pointer',['pointer']);
const message=Module.getGlobalExportByName('objc_msgSend');
const length=new NativeFunction(message,'ulong',['pointer','pointer']);
const bytes=new NativeFunction(message,'pointer',['pointer','pointer']);
const lengthSelector=selRegister(Memory.allocUtf8String('length'));
const bytesSelector=selRegister(Memory.allocUtf8String('bytes'));
let installed=false;
function installObjCHook() {
  if (installed) return;
  const cls=objcGetClass(Memory.allocUtf8String('UVPropertyList'));
  if (cls.isNull()) return;
  const method=getMethod(cls,selRegister(Memory.allocUtf8String('data')));
  if (method.isNull()) return;
  const imp=Process.arch==='arm64' ? getImp(method).strip() : getImp(method);
  const m=Process.findModuleByAddress(imp);
  if (m===null) {emit('capture-error',{error:'Cannot identify method image'});return;}
  hooks.push(Interceptor.attach(imp, { onLeave(retval) {
    if (retval.isNull()) { emit('plist-null',{});return; }
    try {
      const size=Number(length(retval,lengthSelector));
      if (size>65536) {emit('plist-truncated',{bytes:size});return;}
      const address=bytes(retval,bytesSelector);
      send({kind:'plist-data',sequence:++sequence,pid:Process.id,thread:Process.getCurrentThreadId(),timestamp_ms:Date.now(),bytes:size,image:imageIdentity(m)},address.readByteArray(size));
    } catch(e) {emit('capture-error',{error:String(e)});}
  }}));
  installed=true;emit('objc-hook-installed',{image:imageIdentity(m),offset:imp.sub(m.base).toString()});
}
const observer=Process.attachModuleObserver({onAdded(m) { if (m.name==='PreviewsServices') installObjCHook(); }});
emit('ready',{fixture:imageIdentity(fixture)});
