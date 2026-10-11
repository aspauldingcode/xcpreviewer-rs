// Loaded only after Python verifies an owned PreviewLab build-root mapping.
'use strict';
let sequence=0,installed=false,scheduled=false;
function emit(kind,details,data) {
  send(Object.assign({kind,sequence:++sequence,pid:Process.id,thread:Process.getCurrentThreadId(),wall_time_ms:Date.now()},details),data);
}
function moduleInfo(m) {
  let uuid=null;
  try {
    if(m.base.readU32()===0xfeedfacf) {
      let p=m.base.add(32),n=m.base.add(16).readU32();
      for(let i=0;i<Math.min(n,1024);i++) {
        const kind=p.readU32(),size=p.add(4).readU32();if(size<8)break;
        if(kind===0x1b){uuid=Array.from(new Uint8Array(p.add(8).readByteArray(16)),v=>v.toString(16).padStart(2,'0')).join('');break;}
        p=p.add(size);
      }
    }
  } catch(e) {}
  return {name:m.name,path:m.path,base:String(m.base),uuid};
}
function install() {
  if(installed)return;
  try {
    const getClass=new NativeFunction(Module.getGlobalExportByName('objc_getClass'),'pointer',['pointer']);
    const selector=new NativeFunction(Module.getGlobalExportByName('sel_registerName'),'pointer',['pointer']);
    const method=new NativeFunction(Module.getGlobalExportByName('class_getInstanceMethod'),'pointer',['pointer','pointer']);
    const imp=new NativeFunction(Module.getGlobalExportByName('method_getImplementation'),'pointer',['pointer']);
    const cls=getClass(Memory.allocUtf8String('UVPropertyList'));if(cls.isNull())return;
    const m=method(cls,selector(Memory.allocUtf8String('data')));if(m.isNull())return;
    const address=Process.arch==='arm64'?imp(m).strip():imp(m);
    const image=Process.findModuleByAddress(address);if(image===null)return;
    const length=new NativeFunction(Module.getGlobalExportByName('objc_msgSend'),'ulong',['pointer','pointer']);
    const bytes=new NativeFunction(Module.getGlobalExportByName('objc_msgSend'),'pointer',['pointer','pointer']);
    const lengthSel=selector(Memory.allocUtf8String('length')),bytesSel=selector(Memory.allocUtf8String('bytes'));
    Interceptor.attach(address,{onLeave(retval){
      if(retval.isNull())return;
      try {
        const size=Number(length(retval,lengthSel));
        if(size>65536){emit('truncated',{bytes:size});return;}
        emit('plist-data',{bytes:size,image:moduleInfo(image),offset:String(address.sub(image.base)),direction:'serialization; transport direction unknown'},bytes(retval,bytesSel).readByteArray(size));
      } catch(e){emit('capture-error',{error:String(e)});}
    }});
    installed=true;emit('hook-installed',{image:moduleInfo(image),offset:String(address.sub(image.base))});
  } catch(e){emit('hook-unavailable',{error:String(e)});}
}
// Avoid runtime/ObjC calls inside the loader's synchronous module notification.
function scheduleInstall() {
  if(installed||scheduled)return;
  scheduled=true;
  setImmediate(()=>{try{install();}finally{scheduled=false;}});
}
Process.attachModuleObserver({onAdded(m){if(/Preview|SwiftUI|libxpc/i.test(m.name))emit('module-loaded',moduleInfo(m));scheduleInstall();}});
setInterval(scheduleInstall,250);
emit('ready',{coverage:'late attach; requests before attach unknown'});
