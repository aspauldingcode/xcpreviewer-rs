'use strict';
const image=Process.getModuleByName('PreviewsFoundationHost');
if(image.path!=='/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost')throw Error('image path mismatch');
let serial=0;
function caller(p){const offset=p.sub(image.base);const n=offset.toUInt32();return n>=0x2bcc4 && n<0x2c168 ? offset.toString() : null;}
Interceptor.attach(Module.getGlobalExportByName('_os_log_impl'),{
 onEnter(args){this.offset=caller(this.returnAddress);if(this.offset){this.id=++serial;send({event:'native-log-api-enter',id:this.id,caller_offset:this.offset,type:args[2].toUInt32()&255,thread:Process.getCurrentThreadId()});}}
});
Interceptor.attach(Module.getGlobalExportByName('os_log_type_enabled'),{
 onEnter(){this.offset=caller(this.returnAddress);},
 onLeave(value){if(this.offset)send({event:'native-log-enabled-result',caller_offset:this.offset,enabled:value.toUInt32()&1});}
});
send({event:'hooks-ready',image_path:image.path});
