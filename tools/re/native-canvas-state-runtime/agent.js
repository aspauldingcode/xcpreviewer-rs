'use strict';
function uuid(mod){if(mod.base.readU32()!==0xfeedfacf)throw Error('Mach header');let p=mod.base.add(32),value=null;for(let i=0,n=mod.base.add(16).readU32();i<n;i++){const c=p.readU32(),s=p.add(4).readU32();if(s<8)throw Error('load-command bound');if(c===0x1b)value=Array.from(new Uint8Array(p.add(8).readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join('');p=p.add(s);}return value;}
const scenes=Process.getModuleByName('PreviewsScenes'),ui=Process.getModuleByName('PreviewsUI');
if(uuid(scenes)!=='afaf513ac1153755840e1d82b40e7d93'||uuid(ui)!=='0d87b0e2f4453035a9b6b1cf8230e015')throw Error('UUID mismatch');
let serial=0;
Interceptor.attach(scenes.base.add(0x3f694),{onEnter(){this.id=++serial;send({event:'preview-update-enter',id:this.id,thread:Process.getCurrentThreadId()});},onLeave(){send({event:'preview-update-return',id:this.id});}});
Interceptor.attach(ui.base.add(0x19dd4),{onEnter(){this.selected=this.returnAddress.sub(scenes.base).toString()==='0x3f978';if(this.selected){this.id=++serial;send({event:'instance-assignment-helper-enter',id:this.id,thread:Process.getCurrentThreadId(),caller_offset:'0x3f978'});}},onLeave(){if(this.selected)send({event:'instance-assignment-helper-return',id:this.id});}});
send({event:'hooks-ready',scenes_uuid:uuid(scenes),ui_uuid:uuid(ui)});
