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
let mode=CommandLine.arguments.dropFirst().first ?? "invalidate"
let h=makeHandle()
if mode=="invalidate" {
 var p:Probe?=Probe("first");weak var weakProbe=p;let fd=p!.descriptor;let t=add(h,p!);precondition(callbacks.isEmpty);p=nil;precondition(weakProbe != nil);event("caller-probe-dropped",["native_retains":true]);invalidate(h);precondition(callbacks==["first"]);precondition(weakProbe==nil && closed(fd));invalidate(h);precondition(callbacks==["first"]);var late:Probe?=Probe("late");let lt=add(h,late!);precondition(callbacks==["first","late"] && lt.load(as:UInt.self)==0);late=nil;dropToken(lt);dropToken(t);release(h)
} else if mode=="cancel" {
 var p:Probe?=Probe("cancelled");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil;precondition(w != nil);cancel(t);precondition(w==nil && closed(fd) && callbacks.isEmpty);cancel(t);invalidate(h);precondition(callbacks.isEmpty);dropToken(t);release(h)
} else if mode=="owner-loss" {
 var p:Probe?=Probe("owner-loss");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil;weak var wh:AnyObject?=Unmanaged<AnyObject>.fromOpaque(h).takeUnretainedValue();event("handle-release-begin");release(h);event("handle-release-end");precondition(wh==nil && w==nil && closed(fd));cancel(t);precondition(callbacks.isEmpty);dropToken(t)
} else if mode=="reentrant" {
 var p:Probe?=Probe("reentrant");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil;callbackReentry=h;invalidate(h);precondition(callbacks==["reentrant"] && w==nil && closed(fd));dropToken(t);release(h)
} else if mode=="ordering" {
 var a:Probe?=Probe("a"),b:Probe?=Probe("b"),c:Probe?=Probe("c");let fds=[a!.descriptor,b!.descriptor,c!.descriptor];let ts=[add(h,a!),add(h,b!),add(h,c!)];a=nil;b=nil;c=nil;cancel(ts[1]);invalidate(h);precondition(callbacks==["a","c"] && fds.allSatisfy{closed($0)});for t in ts {dropToken(t)};release(h)
} else if mode=="inflight" {
 var p:Probe?=Probe("inflight");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil
 let group=DispatchGroup();group.enter();DispatchQueue.global().async {invalidate(h);group.leave()}
 precondition(callbackEntered.wait(timeout:.now()+2) == .success);cancel(t)
 precondition(w != nil && !closed(fd));event("cancel-returned-callback-still-blocked",["context_alive":w != nil,"fd_open":!closed(fd)])
 callbackMayReturn.signal();precondition(group.wait(timeout:.now()+2) == .success)
 precondition(w==nil && closed(fd) && callbacks==["inflight"]);event("inflight-cleanup-complete",["fd_closed":closed(fd),"context_released":w==nil]);dropToken(t);release(h)
} else if mode=="race" {
 // Keep this outer handle empty and explicitly fulfilled before release.
 invalidate(h);release(h)
 for i in 0..<100 {
  let owner=makeHandle();var p:Probe?=Probe("race-\(i)");weak var w=p;let fd=p!.descriptor;let token=add(owner,p!);p=nil
  let group=DispatchGroup(),start=DispatchSemaphore(value:0)
  for job in 0..<4 {group.enter();DispatchQueue.global().async {precondition(start.wait(timeout:.now()+2) == .success);if job%2==0 {cancel(token)} else {invalidate(owner)};group.leave()}}
  for _ in 0..<4 {start.signal()};precondition(group.wait(timeout:.now()+2) == .success)
  let count=callbacks.filter{$0=="race-\(i)"}.count;precondition(count<=1 && w==nil && closed(fd))
  event("race-round-complete",["round":i,"callbacks":count,"fd_closed":closed(fd),"context_released":w==nil]);dropToken(token);release(owner)
 }
 } else if mode=="cancel-next" {
 var a:Probe?=Probe("cancel-next-a"),b:Probe?=Probe("cancel-next-b");weak var wa=a;weak var wb=b;let fds=[a!.descriptor,b!.descriptor];let ta=add(h,a!),tb=add(h,b!);a=nil;b=nil;dispatchCancelToken=tb
 invalidate(h);precondition(callbacks==["cancel-next-a","cancel-next-b"] && wa==nil && wb==nil && fds.allSatisfy{closed($0)});event("dispatch-cleanup-complete",["context_released":wa==nil && wb==nil,"fds_closed":fds.allSatisfy{closed($0)}]);dropToken(ta);dropToken(tb);release(h)
} else if mode=="add-during-dispatch" {
 var a:Probe?=Probe("add-late-a"),b:Probe?=Probe("add-late-b");weak var wa=a;weak var wb=b;let fds=[a!.descriptor,b!.descriptor];let ta=add(h,a!),tb=add(h,b!);a=nil;b=nil;dispatchAddHandle=h
 invalidate(h);precondition(callbacks==["add-late-a","nested-late","add-late-b"] && wa==nil && wb==nil && fds.allSatisfy{closed($0)});event("dispatch-cleanup-complete",["context_released":wa==nil && wb==nil,"fds_closed":fds.allSatisfy{closed($0)}]);dropToken(ta);dropToken(tb);release(h)
} else if mode=="cancel-admitted" {
 var a:Probe?=Probe("admitted-a"),b:Probe?=Probe("admitted-b");weak var wa=a;weak var wb=b;let fds=[a!.descriptor,b!.descriptor];let ta=add(h,a!),tb=add(h,b!);a=nil;b=nil
 let group=DispatchGroup();group.enter();DispatchQueue.global().async {invalidate(h);group.leave()};precondition(callbackEntered.wait(timeout:.now()+2) == .success)
 precondition(callbacks==["admitted-a"]);cancel(tb);precondition(wb != nil && !closed(fds[1]) && callbacks==["admitted-a"]);event("cancel-returned-next-not-called",["context_alive":wb != nil,"fd_open":!closed(fds[1])]);callbackMayReturn.signal();precondition(group.wait(timeout:.now()+2) == .success)
 precondition(callbacks==["admitted-a","admitted-b"] && wa==nil && wb==nil && fds.allSatisfy{closed($0)});event("dispatch-cleanup-complete",["context_released":wa==nil && wb==nil,"fds_closed":fds.allSatisfy{closed($0)}]);dropToken(ta);dropToken(tb);release(h)
} else if mode=="late-while-blocked" {
 var p:Probe?=Probe("parallel-a");weak var w=p;let fd=p!.descriptor;let token=add(h,p!);p=nil
 let group=DispatchGroup();group.enter();DispatchQueue.global().async {invalidate(h);group.leave()}
 precondition(callbackEntered.wait(timeout:.now()+2) == .success)
 // Second invalidation is not a join of the first dispatch's active callback.
 invalidate(h);precondition(callbacks==["parallel-a"] && w != nil && !closed(fd))
 event("second-invalidate-returned-original-blocked",["context_alive":w != nil,"fd_open":!closed(fd)])
 var late:Probe?=Probe("parallel-late");weak var wl=late;let lateFD=late!.descriptor
 event("cross-thread-late-add-begin");let lt=add(h,late!)
 precondition(lt.load(as:UInt.self)==0 && callbacks==["parallel-a","parallel-late"])
 event("cross-thread-late-add-returned",["has_token":false]);late=nil;dropToken(lt)
 precondition(wl==nil && closed(lateFD) && w != nil && !closed(fd))
 event("late-cleaned-original-blocked",["late_context_released":wl==nil,"late_fd_closed":closed(lateFD),"original_context_alive":w != nil,"original_fd_open":!closed(fd)])
 callbackMayReturn.signal();precondition(group.wait(timeout:.now()+2) == .success)
 precondition(w==nil && closed(fd) && callbacks==["parallel-a","parallel-late"])
 event("parallel-cleanup-complete",["context_released":w==nil,"fd_closed":closed(fd)])
 invalidate(h);precondition(callbacks==["parallel-a","parallel-late"]);dropToken(token);release(h)
} else if mode=="invalidate-deinit-reentry" || mode=="invalidate-deinit-add" {
 var p:Probe?=Probe(mode);weak var w=p;let fd=p!.descriptor;let token=add(h,p!);p=nil;destructionReentry=h
 invalidate(h)
 let expected=mode=="invalidate-deinit-add" ? [mode,"destructor-late"] : [mode]
 precondition(callbacks==expected && w==nil && closed(fd) && destructionReentry==nil)
 event("destructor-cleanup-complete",["context_released":w==nil,"fd_closed":closed(fd)])
 invalidate(h);precondition(callbacks==expected);dropToken(token);release(h)
} else if mode=="self-cancel-drop" || mode=="self-drop" {
 var p:Probe?=Probe(mode);selfTokenProbe=p;selfTokenFD=p!.descriptor;selfTokenContext=UnsafeRawPointer(Unmanaged.passUnretained(p!).toOpaque());selfTokenShouldCancel=(mode=="self-cancel-drop")
 selfToken=add(h,p!);p=nil;precondition(selfTokenProbe != nil)
 invalidate(h)
 precondition(callbacks==[mode] && selfToken==nil && selfTokenProbe==nil && closed(selfTokenFD))
 event("self-cleanup-complete",["context_released":selfTokenProbe==nil,"fd_closed":closed(selfTokenFD)])
 selfTokenContext=nil;invalidate(h);precondition(callbacks==[mode]);release(h)
} else if mode=="cancel-reentry" {
 var p:Probe?=Probe("cancel-reentry");let t=add(h,p!);p=nil;destructionReentry=h;cancel(t);event("destructor-reentry-returned");dropToken(t);invalidate(h);release(h)
} else if mode=="drop-waiting-token" {
 let p=Probe("drop-waiting");let t=add(h,p);dropToken(t);event("after-waiting-token-drop");invalidate(h);precondition(callbacks==["drop-waiting"]);release(h)
} else {fatalError("unknown mode")}
event("pass",["mode":mode,"callbacks":callbacks]);release(UnsafeRawPointer(bitPattern:traceBits)!);trace.deallocate();callsite.deallocate()
