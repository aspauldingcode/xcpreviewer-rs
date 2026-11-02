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
let anchor=ss("$s16PreviewsServices0A17ServiceConnectionCMa",0xb080)
let imageBase=anchor.advanced(by:-0xb080)
func privateFunction(_ o:Int)->UnsafeMutableRawPointer {let p=imageBase.advanced(by:o);precondition(offset(p)==UInt(o) && String(cString:image(p))==servicePath);return p}
for (address,name) in [(0x28f680978,"xpc_connection_activate"),(0x28f680980,"xpc_connection_cancel")] {
 let slot=imageBase.advanced(by:address-0x263300000).load(as:UnsafeMutableRawPointer.self)
 precondition(slot==dlsym(UnsafeMutableRawPointer(bitPattern:-2),name),"source C operation binding")
}
let classMetadata=unsafeBitCast(privateFunction(0x6e00),to:Accessor.self)(0)
let initialize=privateFunction(0x7c84),activate=privateFunction(0x4dfc),send=privateFunction(0x50a4),invalidate=privateFunction(0x37c4)
let classObject:AnyClass=NSClassFromString("_TtC16PreviewsServices13XPCConnection")!
precondition(unsafeBitCast(classObject,to:UnsafeRawPointer.self)==classMetadata)
let allocate=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_allocObject")!
let alloc=unsafeBitCast(allocate,to:(@convention(c)(UnsafeRawPointer,UInt,UInt)->UnsafeMutableRawPointer).self)
func stage(_ s:String){fputs(s+"\n",stderr);fflush(stderr)}
let semaphore=DispatchSemaphore(value:0)
var nativeKind=""
var responseData:Data?=nil,uvPresent=false
var response:NSDictionary?=nil,errorPresent=false,callbackCount=0,errorDomain="",errorCode=0,errorDescription=""
@_cdecl("owned_service_reply_record")
func reply(_ value:UnsafeRawPointer?,_ error:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 if let context=context {Unmanaged<CaptureToken>.fromOpaque(context).takeUnretainedValue().used()}
 callbackCount+=1;errorPresent=error != nil
 if let error=error {
  guard let retain=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRetain") else {fatalError("error retain unavailable")}
  let retained=unsafeBitCast(retain,to:(@convention(c)(UnsafeRawPointer)->UnsafeRawPointer).self)(error)
  let owned=unsafeBitCast(retained,to:Error.self);let ns=owned as NSError
  if let kind=Mirror(reflecting:owned).children.first(where:{$0.label=="kind"}) {nativeKind=String(describing:kind.value)}
  errorDomain=ns.domain;errorCode=ns.code;errorDescription=ns.localizedDescription.replacingOccurrences(of:"0x[0-9a-fA-F]+",with:"(private)",options:.regularExpression)
 }
 if let value=value {uvPresent=true;responseData=owned_uv_data(value) as Data?;if true {response=owned_uv_dictionary(value) as NSDictionary?}}
 semaphore.signal()
}
guard let raw=owned_create_client() else {fatalError("owned XPC create failed")}
stage("raw peer created")
let allocated=alloc(classMetadata,112,7)
precondition(owned_object_size(allocated)==112)
stage("native class allocated")
let pointer=owned_swift_scalar(initialize,raw,nil,nil,nil,allocated)
precondition(pointer==UInt(bitPattern:allocated))
weak var observedNativeConnection:AnyObject?
observedNativeConnection=Unmanaged<AnyObject>.fromOpaque(allocated).takeUnretainedValue()
let instance=UnsafeRawPointer(allocated)
let rawMatches=instance.load(fromByteOffset:16,as:UnsafeRawPointer.self)==UnsafeRawPointer(raw)
precondition(rawMatches)
precondition((24..<112).allSatisfy {instance.load(fromByteOffset:$0,as:UInt8.self)==0})
stage("native initializer returned")
precondition(invoke(activate,nil,nil,instance,nil)==nil)
stage("native activate returned")
guard let uv=owned_uv_create(["ownedRequest":17]) else {fatalError("UV constructor signature unavailable")}
final class CaptureLog {
 let lock=NSLock()
 var events=[String]()
 func record(_ value:String){lock.lock();events.append(value);lock.unlock()}
 func snapshot()->[String]{lock.lock();defer{lock.unlock()};return events}
}
let captureLog=CaptureLog(),captureReleased=DispatchSemaphore(value:0)
final class CaptureToken {
 func used(){captureLog.record("capture-used")}
 deinit {captureLog.record("capture-destroyed");captureReleased.signal()}
}
weak var observedCapture:CaptureToken?
func captureIsAlive()->Bool {observedCapture != nil}
func sendWithOwnedCapture() {
 let token=CaptureToken();observedCapture=token
 let callback=unsafeBitCast(owned_service_reply as @convention(c)()->Void,to:UnsafeRawPointer.self)
 withExtendedLifetime(token) {
  precondition(owned_swift_call3(send,uv,callback,Unmanaged.passUnretained(token).toOpaque(),instance,nil)==nil)
 }
}
sendWithOwnedCapture()
owned_obj_release(uv)
stage("native send returned")
precondition(owned_peer_wait_request())
stage("request reached owned peer; reply pending")
let mode=CommandLine.arguments[1]
let aliveWhilePending=captureIsAlive()
precondition(aliveWhilePending,"Native callback did not retain owned capture")
captureLog.record("pending-after-caller-closure-scope")
precondition(mode=="reply-first" || mode=="remote-close")
guard let release=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_release") else {fatalError("release")}
unsafeBitCast(release,to:(@convention(c)(UnsafeRawPointer)->Void).self)(instance)
captureLog.record("original-connection-reference-dropped-before-trigger")
let nativeAliveAfterOwnerDrop=observedNativeConnection != nil
precondition(nativeAliveAfterOwnerDrop,"Pending reply did not retain native connection")
stage("original native connection owner released while request pending")
if mode=="remote-close" {owned_remote_close();stage("owned remote canceled while reply pending")}
else {owned_peer_reply();stage("owned peer sent valid reply")}
let wait=semaphore.wait(timeout:.now()+3)
let peer=owned_peer_result() ?? [:]
stage("reply wait returned")
let aliveAtReplyWait=captureIsAlive()
owned_obj_release(raw)
owned_peer_close()
let releasedWait=captureReleased.wait(timeout:.now()+3)
let nativeReleaseDeadline=DispatchTime.now().uptimeNanoseconds+3_000_000_000
while observedNativeConnection != nil && DispatchTime.now().uptimeNanoseconds<nativeReleaseDeadline {usleep(1000)}
let nativeAliveAfterCleanup=observedNativeConnection != nil
precondition(!nativeAliveAfterCleanup,"Native connection remained alive through cleanup deadline")
let aliveAfterCleanup=captureIsAlive()
let events=captureLog.snapshot()
stage("owned peer cleanup and capture release wait returned")
var result=[String:Any]()
result["nativeAliveAfterOwnerDrop"]=nativeAliveAfterOwnerDrop
result["nativeAliveAfterCleanup"]=nativeAliveAfterCleanup
result["captureAliveWhilePending"]=aliveWhilePending
result["captureAliveAtReplyWait"]=aliveAtReplyWait
result["captureReleasedAfterCleanup"]=releasedWait == .success
result["captureAliveAfterCleanup"]=aliveAfterCleanup
result["captureEvents"]=events
result["originalReferenceDroppedBeforeTrigger"]=true
result["nativeKind"]=nativeKind
result["mode"]=mode
result["replyTimedOut"]=wait != .success
result["uvPresent"]=uvPresent
result["responseDataPresent"]=responseData != nil
result["responseData"]=responseData ?? Data()
result["callbackCount"]=callbackCount
result["errorPresent"]=errorPresent
result["errorDomain"]=errorDomain
result["errorCode"]=errorCode
result["errorDescription"]=errorDescription
result["response"]=response ?? [:]
result["peer"]=peer
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]));print("native profile completed")
