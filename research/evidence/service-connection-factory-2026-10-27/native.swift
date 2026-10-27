import Foundation
import Darwin
import CoreFoundation
func invoke(_ fn:UnsafeMutableRawPointer,_ arg0:UnsafeRawPointer?,_ arg1:UnsafeRawPointer?,_ context:UnsafeRawPointer?,_ result:UnsafeMutableRawPointer?)->UnsafeMutableRawPointer? {owned_swift_call(fn,arg0,arg1,context,result)}
func offset(_ p:UnsafeMutableRawPointer)->UInt {owned_symbol_offset(p)}
func image(_ p:UnsafeMutableRawPointer)->UnsafePointer<CChar> {owned_symbol_path(p)}
let base="/Applications/Xcode.app/Contents/SharedFrameworks/"
func load(_ name:String)->UnsafeMutableRawPointer {guard let h=dlopen(base+name+".framework/Versions/A/"+name,RTLD_NOW|RTLD_LOCAL) else {fputs(String(cString:dlerror())+"\n",stderr);exit(2)};return h}
func symbol(_ handle:UnsafeMutableRawPointer,_ name:String,_ expected:UInt,_ framework:String)->UnsafeMutableRawPointer {
 guard let p=dlsym(handle,name),offset(p)==expected else {fatalError("symbol identity")}
 let loaded=URL(fileURLWithPath:String(cString:image(p))).resolvingSymlinksInPath().path
 let pinned=URL(fileURLWithPath:base+framework+".framework/Versions/A/"+framework).resolvingSymlinksInPath().path
 precondition(loaded==pinned,"module identity");return p
}
let f=load("PreviewsFoundationHost"),m=load("PreviewsMessagingHost"),p=load("PreviewsPlatforms")
typealias Accessor=@convention(c)(UInt)->UnsafeRawPointer
let fm=symbol(f,"$s22PreviewsFoundationHost12PropertyListVMa",0xab300,"PreviewsFoundationHost")
let mm=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxVMa",0x201f0,"PreviewsMessagingHost")
let fp=unsafeBitCast(fm,to:Accessor.self)(0),mp=unsafeBitCast(mm,to:Accessor.self)(0)
func witness(_ metadata:UnsafeRawPointer,_ index:Int)->UnsafeMutableRawPointer {metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self).load(fromByteOffset:index*8,as:UnsafeMutableRawPointer.self)}
func verify(_ metadata:UnsafeRawPointer) {
 precondition(metadata.load(as:UInt.self)==512 && metadata.load(fromByteOffset:16,as:UInt32.self)==0)
 let table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 precondition(table.load(fromByteOffset:64,as:UInt.self)==8 && table.load(fromByteOffset:72,as:UInt.self)==8 && table.load(fromByteOffset:80,as:UInt32.self)&255==7)
}
verify(fp);verify(mp)
precondition(offset(witness(mp,1))==0x21e20 && offset(witness(fp,1))==0xdbc0)
precondition(offset(witness(fp,2))==0xed44 && offset(witness(fp,4))==0xcb8c)
precondition(MemoryLayout<[String:Any]>.size==8 && MemoryLayout<[String:Any]>.stride==8 && MemoryLayout<[String:Any]>.alignment==8)
guard let release=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRelease") else {fatalError("error release unavailable")}
let errorRelease=unsafeBitCast(release,to:(@convention(c)(UnsafeMutableRawPointer)->Void).self)

let servicePath="/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices"
guard let service=dlopen(servicePath,RTLD_NOW|RTLD_LOCAL) else {fatalError("services missing")}
let matching=(0..<owned_image_count()).filter {i in owned_image_path(i).map{String(cString:$0)==servicePath} ?? false}
precondition(matching.count==1)
let uuid=owned_image_uuid(matching[0])!;precondition((0..<16).map{String(format:"%02x",uuid[$0])}.joined()=="fffb683f59433c2591b272d6e5174fa3")
func ss(_ n:String,_ expected:UInt)->UnsafeMutableRawPointer {
 guard let p=dlsym(service,n),offset(p)==expected,String(cString:image(p))==servicePath else {fatalError("services symbol identity")};return p
}
let ma=ss("$s16PreviewsServices0A17ServiceConnectionCMa",0xb080)
let meta=unsafeBitCast(ma,to:Accessor.self)(0)
let create=ss("$s16PreviewsServices0A17ServiceConnectionC09hostToSimD0ACSo13OS_xpc_object_p_tcfC",0x9abc)
let activate=ss("$s16PreviewsServices0A17ServiceConnectionC8activate8receiveryAA0aC15MessageReceiver_pSg_tF",0xa150)
let send=ss("$s16PreviewsServices0A17ServiceConnectionC4send7message12replyHandlerySo14UVPropertyListC_yAHSg_s5Error_pSgtctF",0xa230)
let invalidate=ss("$s16PreviewsServices0A17ServiceConnectionC10invalidateyyF",0xa12c)
let semaphore=DispatchSemaphore(value:0)
var response:NSDictionary?=nil,errorPresent=false,callbackCount=0,errorDomain="",errorCode=0,errorDescription=""
@_cdecl("owned_service_reply_record")
func reply(_ value:UnsafeRawPointer?,_ error:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 callbackCount+=1;errorPresent=error != nil
 if let error=error {
  guard let retain=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRetain") else {fatalError("error retain unavailable")}
  let retained=unsafeBitCast(retain,to:(@convention(c)(UnsafeRawPointer)->UnsafeRawPointer).self)(error)
  let owned=unsafeBitCast(retained,to:Error.self);let ns=owned as NSError
  errorDomain=ns.domain;errorCode=ns.code;errorDescription=ns.localizedDescription
 }
 if let value=value {response=owned_uv_dictionary(value) as NSDictionary?}
 semaphore.signal()
}
guard let raw=owned_create_client() else {fatalError("owned XPC create failed")}
let pointer=owned_swift_scalar(create,raw,nil,nil,nil,meta);precondition(pointer != 0)
let instance=UnsafeRawPointer(bitPattern:pointer)!
let inner=instance.load(fromByteOffset:16,as:UnsafeRawPointer.self)
let rawMatches=inner.load(fromByteOffset:16,as:UnsafeRawPointer.self)==UnsafeRawPointer(raw)
print("owned wrapper layout",owned_object_size(instance),owned_object_size(inner),"raw matches",rawMatches)
precondition(owned_object_size(instance)==32 && owned_object_size(inner)==112 && rawMatches)
let nilReceiver=UnsafeMutableRawPointer.allocate(byteCount:40,alignment:8);nilReceiver.initializeMemory(as:UInt8.self,repeating:0,count:40)
precondition(invoke(activate,nilReceiver,nil,instance,nil)==nil);nilReceiver.deallocate()
guard let uv=owned_uv_create(["ownedRequest":17]) else {fatalError("UV constructor signature unavailable")}
let callback=unsafeBitCast(owned_service_reply as @convention(c)()->Void,to:UnsafeRawPointer.self)
precondition(owned_swift_call3(send,uv,callback,nil,instance,nil)==nil)
owned_obj_release(uv)
let wait=semaphore.wait(timeout:.now()+3)
let peer=owned_peer_result() ?? [:]
precondition(invoke(invalidate,nil,nil,instance,nil)==nil)
guard let release=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_release") else {fatalError("release")}
unsafeBitCast(release,to:(@convention(c)(UnsafeRawPointer)->Void).self)(instance)
owned_peer_close()
let result:[String:Any]=["replyTimedOut":wait != .success,"callbackCount":callbackCount,"errorPresent":errorPresent,"errorDomain":errorDomain,"errorCode":errorCode,"errorDescription":errorDescription,"response":response ?? [:],"peer":peer]
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]));print("native profile completed")
