import Foundation
import Darwin
let observationLock=NSLock()
let callbackEntered=DispatchSemaphore(value:0),callbackMayReturn=DispatchSemaphore(value:0)
var sequence=0
func event(_ name:String,_ fields:[String:Any]=[:]) {observationLock.lock();defer{observationLock.unlock()};sequence+=1;var d=fields;d["event"]=name;d["seq"]=sequence;d["thread_id"]=pthread_mach_thread_np(pthread_self());d["time_ns"]=DispatchTime.now().uptimeNanoseconds;let data=try! JSONSerialization.data(withJSONObject:d,options:[.sortedKeys]);FileHandle.standardOutput.write(data);FileHandle.standardOutput.write(Data([10]))}
let base="/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost"
guard let lib=dlopen(base,RTLD_NOW|RTLD_LOCAL) else {fatalError(String(cString:dlerror()))}
func sym(_ name:String,_ off:UInt)->UnsafeMutableRawPointer {guard let p=dlsym(lib,name) else {fatalError("missing "+name)};precondition(owned_symbol_offset(p)==off && String(cString:owned_symbol_path(p))==base);return p}
let matching=(0..<owned_image_count()).filter {owned_image_path($0).map{String(cString:$0)==base} ?? false}
precondition(matching.count==1)
let uuid=owned_image_uuid(matching[0])!;precondition((0..<16).map{String(format:"%02x",uuid[$0])}.joined()=="6b75229bde5d3d3794bc75af4f4704c6")
let anchor=sym("$s22PreviewsFoundationHost28ConcurrentInvalidationHandleCMa",0x42148)
let imageBase=anchor.advanced(by:-0x42148)
func fn(_ offset:Int)->UnsafeMutableRawPointer {let p=imageBase.advanced(by:offset);precondition(owned_symbol_offset(p)==UInt(offset));return p}
typealias Accessor=@convention(c)(UInt)->UnsafeRawPointer
let handleMeta=unsafeBitCast(anchor,to:Accessor.self)(0)
let callMeta=unsafeBitCast(sym("$s22PreviewsFoundationHost8CallsiteVMa",0x49998),to:Accessor.self)(0)
let cv=callMeta.load(fromByteOffset:-8,as:UnsafeRawPointer.self);precondition(cv.load(fromByteOffset:64,as:UInt.self)==57)
let callsite=UnsafeMutableRawPointer.allocate(byteCount:64,alignment:8)
owned_callsite_init(sym("$s22PreviewsFoundationHost8CallsiteVyACs12StaticStringV_S2uAEtcfC",0x490ac),callsite)
guard let tokenType=_typeByName("22PreviewsFoundationHost16CancelationTokenVyAA23ConcurrentTokenCallbackVG") else {fatalError("native token metadata unresolved")}
let tm=unsafeBitCast(tokenType,to:UnsafeRawPointer.self),tv=tm.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(tv.load(fromByteOffset:64,as:UInt.self)==24 && tv.load(fromByteOffset:72,as:UInt.self)==24)
let destroy=tv.load(fromByteOffset:8,as:UnsafeMutableRawPointer.self);precondition(owned_symbol_offset(destroy)==0x12a0ac)
let release=unsafeBitCast(dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_release")!,to:(@convention(c)(UnsafeRawPointer)->Void).self)
let alloc=unsafeBitCast(dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_allocObject")!,to:(@convention(c)(UnsafeRawPointer,UInt,UInt)->UnsafeMutableRawPointer).self)
let traceMeta=unsafeBitCast(sym("$s22PreviewsFoundationHost17InvalidationTraceVMa",0x70438),to:Accessor.self)(0)
precondition(traceMeta.load(fromByteOffset:-8,as:UnsafeRawPointer.self).load(fromByteOffset:64,as:UInt.self)==8)
let empty=sym("$s22PreviewsFoundationHost17InvalidationTraceV5emptyACvgZ",0x4b40)
let trace=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
precondition(owned_swift_call(empty,traceMeta,nil,nil,trace)==nil)
let traceBits=trace.load(as:UInt.self)
event("native-ready",["token_size":24,"trace_size":8,"pid":getpid()])
func makeHandle()->UnsafeMutableRawPointer {let p=alloc(handleMeta,40,7);let mode=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);mode.initializeMemory(as:UInt8.self,repeating:0,count:24);mode.storeBytes(of:UInt8(2),toByteOffset:16,as:UInt8.self);let v=owned_handle_init(fn(0x41df0),p,mode,callsite);precondition(v==p);mode.deallocate();event("handle-created");return p}
var callbacks=[String]()
var callbackReentry:UnsafeMutableRawPointer?
var destructionReentry:UnsafeMutableRawPointer?
var dispatchCancelToken:UnsafeMutableRawPointer?
var dispatchAddHandle:UnsafeMutableRawPointer?
// These controls never recover a strong Probe local inside the callback.
var selfTokenContext:UnsafeRawPointer?
var selfToken:UnsafeMutableRawPointer?
weak var selfTokenProbe:Probe?
var selfTokenFD:Int32 = -1
var selfTokenShouldCancel=false
final class Probe {
 let name:String;let descriptor:Int32
 init(_ name:String){self.name=name;descriptor=open("/dev/null",O_RDONLY);precondition(descriptor>=0);event("probe-created",["name":name,"fd":descriptor])}
 deinit {let rc=close(descriptor);event("probe-deinit",["name":name,"fd":descriptor,"close_result":rc]);if (name=="cancel-reentry" || name=="invalidate-deinit-reentry"),let h=destructionReentry {destructionReentry=nil;event("destructor-reentry-begin");invalidate(h);event("destructor-reentry-end")};if name=="invalidate-deinit-add",let h=destructionReentry {destructionReentry=nil;event("destructor-add-begin");var late:Probe?=Probe("destructor-late");weak var w=late;let fd=late!.descriptor;let token=add(h,late!);precondition(token.load(as:UInt.self)==0 && callbacks==["invalidate-deinit-add","destructor-late"]);event("destructor-add-returned",["has_token":false]);late=nil;precondition(w==nil && closed(fd));dropToken(token);event("destructor-add-end",["context_released":w==nil,"fd_closed":closed(fd)])}}
}
@_cdecl("owned_observer_record")
func record(_ context:UnsafeRawPointer?,_ trace:UnsafeRawPointer?){
 if let expected=selfTokenContext, context==expected {
  precondition(trace != nil);let name=selfTokenShouldCancel ? "self-cancel-drop" : "self-drop"
  observationLock.lock();callbacks.append(name);observationLock.unlock();event("callback",["name":name])
  guard let token=selfToken else {preconditionFailure("missing owned token")};selfToken=nil
  if selfTokenShouldCancel {cancel(token);cancel(token)}
  dropToken(token)
  precondition(selfTokenProbe != nil && !closed(selfTokenFD))
  event("self-token-dropped-context-live",["context_alive":selfTokenProbe != nil,"fd_open":!closed(selfTokenFD),"cancelled":selfTokenShouldCancel])
  event("self-callback-returning");return
 }
 let p=Unmanaged<Probe>.fromOpaque(context!).takeUnretainedValue();precondition(trace != nil);observationLock.lock();callbacks.append(p.name);observationLock.unlock();event("callback",["name":p.name]);if p.name=="inflight" || p.name=="admitted-a" || p.name=="parallel-a" {event("callback-blocked");callbackEntered.signal();precondition(callbackMayReturn.wait(timeout:.now()+2) == .success);event("callback-unblocked")};if p.name=="cancel-next-a",let t=dispatchCancelToken {dispatchCancelToken=nil;event("callback-cancel-next-begin");cancel(t);event("callback-cancel-next-end")};if p.name=="add-late-a",let owner=dispatchAddHandle {dispatchAddHandle=nil;var late:Probe?=Probe("nested-late");weak var w=late;let fd=late!.descriptor;event("callback-add-late-begin");let token=add(owner,late!);precondition(token.load(as:UInt.self)==0 && callbacks==["add-late-a","nested-late"]);event("callback-add-late-returned",["has_token":false]);late=nil;precondition(w==nil && closed(fd));dropToken(token);event("callback-add-late-end",["context_released":w==nil,"fd_closed":closed(fd)])};if p.name=="reentrant",let h=callbackReentry {callbackReentry=nil;event("callback-reentry-begin");invalidate(h);event("callback-reentry-end")}}
func add(_ h:UnsafeMutableRawPointer,_ p:Probe)->UnsafeMutableRawPointer {let t=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);t.initializeMemory(as:UInt8.self,repeating:0xcc,count:24);owned_add_observer(fn(0xbf014),h,unsafeBitCast(owned_observer_callback as @convention(c)()->Void,to:UnsafeMutableRawPointer.self),Unmanaged.passUnretained(p).toOpaque(),t);event("registered",["name":p.name,"has_token":t.load(as:UInt.self) != 0]);return t}
func invalidate(_ h:UnsafeMutableRawPointer){event("invalidate-begin");let ref=UnsafeMutablePointer<UnsafeMutableRawPointer>.allocate(capacity:1);ref.initialize(to:h);precondition(owned_swift_call(fn(0xbfcc8),callsite,trace,ref,nil)==nil);ref.deinitialize(count:1);ref.deallocate();event("invalidate-end")}
func cancel(_ t:UnsafeMutableRawPointer){event("cancel-begin");precondition(owned_swift_call(fn(0x12993c),callsite,tm,t,nil)==nil);event("cancel-end")}
func dropToken(_ t:UnsafeMutableRawPointer){if t.load(as:UInt.self) != 0 {event("token-destroy-begin");precondition(owned_swift_call(destroy,t,tm,nil,nil)==nil);event("token-destroy-end")};t.deallocate()}
func closed(_ fd:Int32)->Bool {errno=0;return fcntl(fd,F_GETFD) == -1 && errno==EBADF}
// Minimum metadata/VWT interface qualification; no new native function body recovered.
struct OwnedCopyValue { let a:Probe;let b:Probe;let c:Probe }
func initializeCopy(_ fn:UnsafeMutableRawPointer,_ source:UnsafeMutableRawPointer,_ meta:UnsafeRawPointer)->UnsafeMutableRawPointer {
 let size=meta.load(fromByteOffset:-8,as:UnsafeRawPointer.self).load(fromByteOffset:64,as:UInt.self);precondition(size==24)
 let dest=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);dest.initializeMemory(as:UInt8.self,repeating:0xcc,count:24)
 let returned=owned_swift_scalar(fn,dest,source,meta,nil,nil);precondition(returned==UInt(bitPattern:dest));return dest
}
func copyToken(_ token:UnsafeMutableRawPointer)->UnsafeMutableRawPointer {
 precondition(token.load(as:UInt.self) != 0)
 let fn=tv.load(fromByteOffset:16,as:UnsafeMutableRawPointer.self),path=String(cString:owned_symbol_path(fn))
 precondition(path==base || path=="/usr/lib/swift/libswiftCore.dylib")
 let copy=initializeCopy(fn,token,tm);precondition(copy.load(as:UInt.self) != 0)
 event("token-copy-complete",["vwt_slot_byte_offset":16,"copy_image":URL(fileURLWithPath:path).lastPathComponent,"copy_function_image_offset":owned_symbol_offset(fn)])
 return copy
}
let mode=CommandLine.arguments.dropFirst().first ?? "owned-copy-abi"
if mode=="owned-copy-abi" {
 var p:Probe?=Probe("owned-copy-abi");weak var weakProbe=p;let fd=p!.descriptor
 let original=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);original.assumingMemoryBound(to:OwnedCopyValue.self).initialize(to:OwnedCopyValue(a:p!,b:p!,c:p!));p=nil
 let meta=unsafeBitCast(OwnedCopyValue.self,to:UnsafeRawPointer.self),witness=meta.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 precondition(witness.load(fromByteOffset:64,as:UInt.self)==24 && witness.load(fromByteOffset:72,as:UInt.self)==24)
 let copy=initializeCopy(witness.load(fromByteOffset:16,as:UnsafeMutableRawPointer.self),original,meta)
 original.assumingMemoryBound(to:OwnedCopyValue.self).deinitialize(count:1);original.deallocate()
 precondition(weakProbe != nil && !closed(fd));event("owned-original-destroyed-copy-live",["context_alive":weakProbe != nil,"fd_open":!closed(fd)])
 copy.assumingMemoryBound(to:OwnedCopyValue.self).deinitialize(count:1);copy.deallocate()
 precondition(weakProbe==nil && closed(fd));event("owned-copy-abi-cleanup",["context_released":weakProbe==nil,"fd_closed":closed(fd)])
} else {
 let h=makeHandle();let name=mode=="copy-inflight" ? "inflight" : mode
 var p:Probe?=Probe(name);weak var w=p;let fd=p!.descriptor;let original=add(h,p!);p=nil;let copy=copyToken(original)
 if mode=="copy-invalidate" {
  dropToken(original);precondition(w != nil && !closed(fd));event("original-token-dropped-copy-kept",["context_alive":w != nil,"fd_open":!closed(fd)])
  invalidate(h);precondition(callbacks==[name] && w==nil && closed(fd));cancel(copy);dropToken(copy);release(h)
 } else if mode=="copy-cancel" {
  cancel(original);precondition(w==nil && closed(fd) && callbacks.isEmpty);event("original-cancelled-copy-kept",["context_released":w==nil,"fd_closed":closed(fd)])
  cancel(copy);invalidate(h);precondition(callbacks.isEmpty);dropToken(original);dropToken(copy);release(h)
 } else if mode=="copy-drop-both" {
  dropToken(original);dropToken(copy);precondition(w != nil && !closed(fd));event("both-tokens-dropped-context-live",["context_alive":w != nil,"fd_open":!closed(fd)])
  invalidate(h);precondition(callbacks==[name] && w==nil && closed(fd));release(h)
 } else if mode=="copy-owner-loss" {
  weak var owner:AnyObject?=Unmanaged<AnyObject>.fromOpaque(h).takeUnretainedValue();event("handle-release-begin");release(h);event("handle-release-end")
  precondition(owner==nil && w==nil && closed(fd));event("owner-lost-copies-kept",["owner_released":owner==nil,"context_released":w==nil,"fd_closed":closed(fd)])
  cancel(original);cancel(copy);precondition(callbacks.isEmpty);dropToken(original);dropToken(copy)
 } else if mode=="copy-inflight" {
  let group=DispatchGroup();group.enter();DispatchQueue.global().async {invalidate(h);group.leave()}
  precondition(callbackEntered.wait(timeout:.now()+2) == .success);cancel(copy);dropToken(original);dropToken(copy)
  precondition(w != nil && !closed(fd));event("copies-dropped-callback-blocked",["context_alive":w != nil,"fd_open":!closed(fd)])
  callbackMayReturn.signal();precondition(group.wait(timeout:.now()+2) == .success);precondition(callbacks==["inflight"] && w==nil && closed(fd));release(h)
 } else {fatalError("unknown mode")}
 precondition(w==nil && closed(fd));event("copy-control-cleanup",["context_released":w==nil,"fd_closed":closed(fd)])
}
event("pass",["mode":mode,"callbacks":callbacks]);release(UnsafeRawPointer(bitPattern:traceBits)!);trace.deallocate();callsite.deallocate()
