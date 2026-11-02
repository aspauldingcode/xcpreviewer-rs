import Foundation
import Darwin
var sequence=0
func event(_ name:String,_ fields:[String:Any]=[:]) {sequence+=1;var d=fields;d["event"]=name;d["seq"]=sequence;d["time_ns"]=DispatchTime.now().uptimeNanoseconds;let data=try! JSONSerialization.data(withJSONObject:d,options:[.sortedKeys]);FileHandle.standardOutput.write(data);FileHandle.standardOutput.write(Data([10]))}
let base="/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost"
guard let lib=dlopen(base,RTLD_NOW|RTLD_LOCAL) else {fatalError(String(cString:dlerror()))}
func sym(_ name:String,_ off:UInt)->UnsafeMutableRawPointer {guard let p=dlsym(lib,name) else {fatalError("missing "+name)};precondition(owned_symbol_offset(p)==off && String(cString:owned_symbol_path(p))==base);return p}
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
let traceBits=owned_swift_scalar(empty,traceMeta,nil,nil,nil,nil)
let trace=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8);trace.storeBytes(of:traceBits,as:UInt.self)
event("native-ready",["token_size":24,"trace_size":8,"pid":getpid()])
func makeHandle()->UnsafeMutableRawPointer {let p=alloc(handleMeta,40,7);let mode=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);mode.initializeMemory(as:UInt8.self,repeating:0,count:24);mode.storeBytes(of:UInt8(2),toByteOffset:16,as:UInt8.self);let v=owned_handle_init(fn(0x41df0),p,mode,callsite);precondition(v==p);mode.deallocate();event("handle-created");return p}
var callbacks=[String]()
final class Probe {
 let name:String;let descriptor:Int32
 init(_ name:String){self.name=name;descriptor=open("/dev/null",O_RDONLY);precondition(descriptor>=0);event("probe-created",["name":name,"fd":descriptor])}
 deinit {let rc=close(descriptor);event("probe-deinit",["name":name,"fd":descriptor,"close_result":rc])}
}
@_cdecl("owned_observer_record")
func record(_ context:UnsafeRawPointer?,_ trace:UnsafeRawPointer?){let p=Unmanaged<Probe>.fromOpaque(context!).takeUnretainedValue();precondition(trace != nil);callbacks.append(p.name);event("callback",["name":p.name])}
func add(_ h:UnsafeMutableRawPointer,_ p:Probe)->UnsafeMutableRawPointer {let t=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);t.initializeMemory(as:UInt8.self,repeating:0xcc,count:24);owned_add_observer(fn(0xbf014),h,unsafeBitCast(owned_observer_callback as @convention(c)()->Void,to:UnsafeMutableRawPointer.self),Unmanaged.passUnretained(p).toOpaque(),t);event("registered",["name":p.name,"has_token":t.load(as:UInt.self) != 0]);return t}
func invalidate(_ h:UnsafeMutableRawPointer){event("invalidate-begin");let ref=UnsafeMutablePointer<UnsafeMutableRawPointer>.allocate(capacity:1);ref.initialize(to:h);precondition(owned_swift_call(fn(0xbfcc8),callsite,trace,ref,nil)==nil);ref.deinitialize(count:1);ref.deallocate();event("invalidate-end")}
func cancel(_ t:UnsafeMutableRawPointer){event("cancel-begin");precondition(owned_swift_call(fn(0x12993c),callsite,tm,t,nil)==nil);event("cancel-end")}
func dropToken(_ t:UnsafeMutableRawPointer){if t.load(as:UInt.self) != 0 {event("token-destroy-begin");precondition(owned_swift_call(destroy,t,tm,nil,nil)==nil);event("token-destroy-end")};t.deallocate()}
func closed(_ fd:Int32)->Bool {errno=0;return fcntl(fd,F_GETFD) == -1 && errno==EBADF}
let mode=CommandLine.arguments.dropFirst().first ?? "invalidate"
do { let warm=Probe("prewarm"); withExtendedLifetime(warm) {} }
let h=makeHandle()
if mode=="invalidate" {
 var p:Probe?=Probe("first");weak var weakProbe=p;let fd=p!.descriptor;let t=add(h,p!);precondition(callbacks.isEmpty);p=nil;precondition(weakProbe != nil);event("caller-probe-dropped",["native_retains":true]);invalidate(h);precondition(callbacks==["first"]);precondition(weakProbe==nil && closed(fd));invalidate(h);precondition(callbacks==["first"]);var late:Probe?=Probe("late");let lt=add(h,late!);precondition(callbacks==["first","late"] && lt.load(as:UInt.self)==0);late=nil;dropToken(lt);dropToken(t);release(h)
} else if mode=="cancel" {
 var p:Probe?=Probe("cancelled");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil;precondition(w != nil);cancel(t);precondition(w==nil && closed(fd) && callbacks.isEmpty);cancel(t);invalidate(h);precondition(callbacks.isEmpty);dropToken(t);release(h)
} else if mode=="owner-loss" {
 var p:Probe?=Probe("owner-loss");weak var w=p;let fd=p!.descriptor;let t=add(h,p!);p=nil;weak var wh:AnyObject?=Unmanaged<AnyObject>.fromOpaque(h).takeUnretainedValue();event("handle-release-begin");release(h);event("handle-release-end");precondition(wh==nil && w==nil && closed(fd));cancel(t);precondition(callbacks.isEmpty);dropToken(t)
} else if mode=="drop-waiting-token" {
 let p=Probe("drop-waiting");let t=add(h,p);dropToken(t);event("after-waiting-token-drop");invalidate(h);release(h)
} else {fatalError("unknown mode")}
event("pass",["mode":mode,"callbacks":callbacks]);release(UnsafeRawPointer(bitPattern:traceBits)!);trace.deallocate();callsite.deallocate()
