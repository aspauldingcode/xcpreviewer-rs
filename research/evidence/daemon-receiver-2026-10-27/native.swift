import Foundation
import Darwin
func offset(_ p:UnsafeMutableRawPointer)->UInt {owned_symbol_offset(p)}
func image(_ p:UnsafeMutableRawPointer)->String {String(cString:owned_symbol_path(p))}
let base="/Applications/Xcode.app/Contents/SharedFrameworks/"
func load(_ name:String)->UnsafeMutableRawPointer {guard let h=dlopen(base+name+".framework/Versions/A/"+name,RTLD_NOW|RTLD_LOCAL) else {fatalError("load")};return h}
func symbol(_ h:UnsafeMutableRawPointer,_ name:String,_ expected:UInt,_ framework:String)->UnsafeMutableRawPointer {let p=dlsym(h,name)!;precondition(offset(p)==expected && image(p).hasSuffix("/"+framework));return p}
let m=load("PreviewsMessagingHost"),p=load("PreviewsPlatforms")
typealias Accessor=@convention(c)(UInt)->UnsafeRawPointer
let role=unsafeBitCast(symbol(p,"$s17PreviewsPlatforms16DaemonClientRoleVMa",0x14074,"PreviewsPlatforms"),to:Accessor.self)(0)
let roleConformance=symbol(p,"$s17PreviewsPlatforms16DaemonClientRoleV0A13MessagingHost0c10ConnectionE0AAMc",0x480d0,"PreviewsPlatforms")
let get=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_getWitnessTable")!;precondition(image(get).hasSuffix("/libswiftCore.dylib"))
typealias GetWitness=@convention(c)(UnsafeRawPointer,UnsafeRawPointer,UnsafeRawPointer?)->UnsafeRawPointer
let witness=unsafeBitCast(get,to:GetWitness.self)
let roleWitness=witness(roleConformance,role,nil)
func entries(_ w:UnsafeRawPointer,_ n:Int)->[String] {(0..<n).map{String(offset(w.load(fromByteOffset:$0*8,as:UnsafeMutableRawPointer.self)),radix:16)}}
precondition(entries(roleWitness,3)==["480d0","13448","13514"])
let anchor=symbol(m,"$s21PreviewsMessagingHost16LazyPropertyListOMa",0x6e960,"PreviewsMessagingHost")
let nativeBase=anchor.advanced(by:-0x6e960)
func local(_ offsetValue:Int)->UnsafeMutableRawPointer {let address=nativeBase.advanced(by:offsetValue);precondition(offset(address)==offsetValue && image(address).hasSuffix("/PreviewsMessagingHost"));return address}
let ma=local(0x75670)
typealias Generic=@convention(c)(UInt,UnsafeRawPointer,UnsafeRawPointer,UnsafeRawPointer?)->UnsafeRawPointer
let receiver=unsafeBitCast(ma,to:Generic.self)(0,role,roleWitness,nil)
precondition(receiver.load(fromByteOffset:16,as:UnsafeRawPointer.self)==role && receiver.load(fromByteOffset:24,as:UnsafeRawPointer.self)==roleWitness)
let table=receiver.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(receiver.load(as:UInt.self)==512 && table.load(fromByteOffset:64,as:UInt.self)==16 && table.load(fromByteOffset:72,as:UInt.self)==16 && table.load(fromByteOffset:80,as:UInt32.self)&255==7 && receiver.load(fromByteOffset:32,as:UInt32.self)==0)
let con=local(0xbd0e0)
let wt=witness(con,receiver,nil);precondition(entries(wt,3)==["bd0e0","7519c","751ac"])

let f=load("PreviewsFoundationHost")
let fp=unsafeBitCast(symbol(f,"$s22PreviewsFoundationHost12PropertyListVMa",0xab300,"PreviewsFoundationHost"),to:Accessor.self)(0)
func vw(_ metadata:UnsafeRawPointer,_ index:Int)->UnsafeMutableRawPointer {metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self).load(fromByteOffset:index*8,as:UnsafeMutableRawPointer.self)}
func invoke(_ fn:UnsafeMutableRawPointer,_ a:UnsafeRawPointer?,_ b:UnsafeRawPointer?,_ context:UnsafeRawPointer?,_ result:UnsafeMutableRawPointer?)->UnsafeMutableRawPointer? {owned_swift_call(fn,a,b,context,result)}
let ft=fp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(fp.load(as:UInt.self)==512 && ft.load(fromByteOffset:64,as:UInt.self)==8 && ft.load(fromByteOffset:72,as:UInt.self)==8 && ft.load(fromByteOffset:80,as:UInt32.self)&255==7 && offset(vw(fp,1))==0xdbc0)
let lazy=unsafeBitCast(anchor,to:Accessor.self)(0),lt=lazy.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
let lazySize=lt.load(fromByteOffset:64,as:UInt.self),lazyStride=lt.load(fromByteOffset:72,as:UInt.self)
precondition(lazy.load(as:UInt.self)==513 && lazySize==17 && lazyStride==24 && lt.load(fromByteOffset:80,as:UInt32.self)&255==7)
let rp=unsafeBitCast(symbol(m,"$s21PreviewsMessagingHost14TransportReplyVMa",0x3fc80,"PreviewsMessagingHost"),to:Accessor.self)(0)
precondition(rp.load(fromByteOffset:-8,as:UnsafeRawPointer.self).load(fromByteOffset:64,as:UInt.self)==24)
let getter=symbol(m,"$s21PreviewsMessagingHost16LazyPropertyListO08propertyF00a10FoundationC00eF0Vvg",0x6e998,"PreviewsMessagingHost")
let unit=local(0x3dbd8)
let errorRelease=unsafeBitCast(dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRelease")!,to:(@convention(c)(UnsafeRawPointer)->Void).self)
let errorRetain=unsafeBitCast(dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRetain")!,to:(@convention(c)(UnsafeRawPointer)->UnsafeRawPointer).self)
func clean(_ s:String)->String {s.replacingOccurrences(of:"\\(unknown context at \\$[0-9a-fA-F]+\\)",with:"(private)",options:.regularExpression)}
var lazyCopy:UnsafeMutableRawPointer?=nil,replyCopy:UnsafeMutableRawPointer?=nil,relayCalls=0,encoded=[[String:Any]]()
@_cdecl("owned_receiver_record")
func record(_ value:UnsafeRawPointer?,_ reply:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 precondition(value != nil && reply != nil && context==nil && lazyCopy==nil && replyCopy==nil)
 let copy=UnsafeMutableRawPointer.allocate(byteCount:Int(lazyStride),alignment:8)
 precondition(owned_swift_call3(vw(lazy,2),copy,value,lazy,nil,nil)==nil);lazyCopy=copy
 let tag=owned_swift_scalar(vw(rp,6),reply,UnsafeRawPointer(bitPattern:1),rp,nil,nil)
 precondition(tag==0 || tag==1)
 if tag==0 {let r=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8);precondition(owned_swift_call3(vw(rp,2),r,reply,rp,nil,nil)==nil);replyCopy=r}
 relayCalls+=1
}
@_cdecl("owned_encoded_record")
func encodedRecord(_ uv:UnsafeRawPointer?,_ error:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 precondition(context==nil)
 var result:[String:Any]=["payloadPresent":uv != nil,"errorPresent":error != nil]
 if let uv=uv {let data=Unmanaged<NSData>.fromOpaque(owned_uv_summary(uv)!).takeRetainedValue() as Data;result["summary"]=try! PropertyListSerialization.propertyList(from:data,format:nil)}
 if let error=error {let owned=unsafeBitCast(errorRetain(error),to:Error.self),ns=owned as NSError;result["errorType"]=clean(String(reflecting:type(of:owned)));result["errorDomain"]=clean(ns.domain);result["errorCode"]=ns.code}
 encoded.append(result)
}
let value=UnsafeMutableRawPointer.allocate(byteCount:16,alignment:8)
value.storeBytes(of:unsafeBitCast(owned_receiver_adapter as @convention(c)()->Void,to:UnsafeRawPointer.self),as:UnsafeRawPointer.self);value.storeBytes(of:UnsafeRawPointer?.none,toByteOffset:8,as:UnsafeRawPointer?.self)
let handler=unsafeBitCast(owned_encoded_adapter as @convention(c)()->Void,to:UnsafeRawPointer.self)
let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),format:nil) as! [[String:Any]]
var rows=[[String:Any]](),carriers=[[String:Any]](),lazyDestroyed=0,replyDestroyed=0,parseErrorsReleased=0
for row in input {
 let data=row["data"] as! Data,mode=row["mode"] as! String
 let before=relayCalls,callbacks=encoded.count
 autoreleasepool {
  let request=try! PropertyListSerialization.data(fromPropertyList:["owned":"daemon receiver"],format:.binary,options:0) as NSData,response=data as NSData
  var receipt:UnsafeMutableRawPointer?=nil
  let uvPointer=withExtendedLifetime((request,response)) {owned_exchange_uv(Unmanaged.passUnretained(request).toOpaque(),Unmanaged.passUnretained(response).toOpaque(),&receipt)!}
  let uv=Unmanaged<AnyObject>.fromOpaque(uvPointer).takeRetainedValue()
  let receiptData=Unmanaged<NSData>.fromOpaque(receipt!).takeRetainedValue() as Data;carriers.append(try! PropertyListSerialization.propertyList(from:receiptData,format:nil) as! [String:Any])
  withExtendedLifetime(uv) {
   if mode=="oneway" {owned_receive_oneway(wt.load(fromByteOffset:8,as:UnsafeMutableRawPointer.self),uvPointer,receiver,value)}
   else {owned_receive_reply(wt.load(fromByteOffset:16,as:UnsafeMutableRawPointer.self),uvPointer,handler,nil,receiver,value)}
  }
 }
 precondition(relayCalls==before+1 && encoded.count==callbacks && lazyCopy != nil)
 let type=unsafeBitCast(lazy,to:Any.Type.self)
 func load<T>(_ type:T.Type)->Any {lazyCopy!.load(as:T.self)}
 let owned=_openExistential(type,do:load);precondition(String(reflecting:Swift.type(of:owned))=="PreviewsMessagingHost.LazyPropertyList")
 let children=Array(Mirror(reflecting:owned).children);precondition(children.count==1 && children[0].label=="serialized");let bytes=children[0].value as! Data;precondition(bytes==data)
 let parsed=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 let failure=invoke(getter,nil,nil,lazyCopy,parsed)
 var result:[String:Any]=["case":row["case"]!,"mode":mode,"serializedBytes":bytes,"replyPresent":replyCopy != nil,"parseAccepted":failure==nil]
 if let failure=failure {errorRelease(failure);parseErrorsReleased+=1}
 else {result["canonical"]=parsed.assumingMemoryBound(to:[String:Any].self).pointee;precondition(invoke(vw(fp,1),parsed,fp,nil,nil)==nil)}
 parsed.deallocate()
 precondition(invoke(vw(lazy,1),lazyCopy,lazy,nil,nil)==nil);lazyCopy!.deallocate();lazyCopy=nil;lazyDestroyed+=1
 if let reply=replyCopy {if mode=="send" {owned_reply_unit(unit,reply)};precondition(invoke(vw(rp,1),reply,rp,nil,nil)==nil);reply.deallocate();replyCopy=nil;replyDestroyed+=1}
 result["encodedReplies"]=Array(encoded.dropFirst(callbacks));rows.append(result)
}
precondition(invoke(vw(receiver,1),value,receiver,nil,nil)==nil);value.deallocate()
var images=[String:String]()
for i in 0..<owned_image_count() {guard let path=owned_image_path(i) else {continue};let n=String(cString:path);if !n.contains("Previews") && !n.contains("libswiftCore.") {continue};let uuid=owned_image_uuid(i)!;images[n]=(0..<16).map{String(format:"%02x",uuid[$0])}.joined()}
let result:[String:Any]=["rows":rows,"carrierReceipts":carriers,"runtimeImages":images,"relayCalls":relayCalls,"encodedCallbackCalls":encoded.count,"lazyCopiesDestroyed":lazyDestroyed,"replyCopiesDestroyed":replyDestroyed,"parseErrorsReleased":parseErrorsReleased,"lazySize":lazySize,"lazyStride":lazyStride,"receiverSize":16,"receiverStride":16,"receiverWitnessOffsets":entries(wt,3)]
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("rows",rows.count,"callbacks",encoded.count,"lazy",lazySize,lazyStride)
