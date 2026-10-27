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

let um=symbol(p,"$s17PreviewsPlatforms34PreviewShellModernUpdaterInterfaceVMa",0x32fa0,"PreviewsPlatforms")
let up=unsafeBitCast(um,to:Accessor.self)(0),ut=up.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(up.load(as:UInt.self)==512 && ut.load(fromByteOffset:64,as:UInt.self)==52 && ut.load(fromByteOffset:72,as:UInt.self)==56 && ut.load(fromByteOffset:80,as:UInt32.self)&255==7)
precondition(up.load(fromByteOffset:16,as:UInt32.self)==0 && up.load(fromByteOffset:20,as:UInt32.self)==40)
let sm=symbol(m,"$s21PreviewsMessagingHost18ShellUpdatePayloadVMa",0x22930,"PreviewsMessagingHost")
let sp=unsafeBitCast(sm,to:Accessor.self)(0),st=sp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(st.load(fromByteOffset:64,as:UInt.self)==176 && st.load(fromByteOffset:72,as:UInt.self)==176)
let decode=symbol(m,"$s21PreviewsMessagingHost18ShellUpdatePayloadV17propertyListValueAC0a10FoundationC008PropertyH0V_tKcfC",0x23570,"PreviewsMessagingHost")
let encode=symbol(m,"$s21PreviewsMessagingHost14ServiceMessageV17propertyListValue0a10FoundationC008PropertyG0Vvg",0x5f454,"PreviewsMessagingHost")
let update=symbol(p,"$s17PreviewsPlatforms34PreviewShellModernUpdaterInterfaceV6update0H7Payload0A14FoundationHost6FutureCyAF12PropertyListVG0a9MessagingK00d6UpdateI0V_tF",0x34384,"PreviewsPlatforms")
let rm=symbol(m,"$s21PreviewsMessagingHost14TransportReplyVMa",0x3fc80,"PreviewsMessagingHost")
let rp=unsafeBitCast(rm,to:Accessor.self)(0),rt=rp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(rp.load(as:UInt.self)==512 && rt.load(fromByteOffset:64,as:UInt.self)==24 && rt.load(fromByteOffset:72,as:UInt.self)==24)
precondition(offset(witness(rp,1))==0x40f10 && offset(witness(rp,2))==0x40f50)
let sendUnit=symbol(m,"$s21PreviewsMessagingHost14TransportReplyV4send4file4line6column8functionys12StaticStringV_S2uAJtF",0x3dbd8,"PreviewsMessagingHost")
let succeeded=symbol(f,"$s22PreviewsFoundationHost6FutureC23hasFinishedSuccessfullySbvg",0xfc348,"PreviewsFoundationHost")
var currentMode="none",replyCopy:UnsafeMutableRawPointer?=nil
var received=[[String:Any]]()
@_cdecl("owned_transport_record")
func record(_ message:UnsafeRawPointer?,_ reply:UnsafeRawPointer?,_ metadata:UnsafeRawPointer?,_ witnessPointer:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 precondition(message != nil && reply != nil && metadata==unsafeBitCast(UInt64.self,to:UnsafeRawPointer.self))
 precondition(context!.load(as:UInt64.self)==0x3132333435363738)
 let raw=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(encode,nil,nil,message,raw)==nil)
 received.append(raw.assumingMemoryBound(to:[String:Any].self).pointee)
 if currentMode=="immediate" {owned_reply_unit(sendUnit,reply)}
 if currentMode=="delayed" {
   precondition(replyCopy==nil)
   let copy=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
   precondition(owned_swift_call3(witness(rp,2),copy,reply,rp,nil,nil)==nil);replyCopy=copy
 }
 precondition(invoke(witnessForPlist(),raw,fp,nil,nil)==nil);raw.deallocate()
}
func witnessForPlist()->UnsafeMutableRawPointer {witness(fp,1)}
let wt=UnsafeMutablePointer<UnsafeRawPointer?>.allocate(capacity:3);wt.initialize(repeating:nil,count:3)
wt[2]=unsafeBitCast(owned_transport_witness as @convention(c)()->Void,to:UnsafeRawPointer.self)
let instance=UnsafeMutableRawPointer.allocate(byteCount:56,alignment:8);instance.initializeMemory(as:UInt8.self,repeating:0,count:56)
instance.storeBytes(of:UInt64(0x3132333435363738),as:UInt64.self)
instance.storeBytes(of:unsafeBitCast(UInt64.self,to:UnsafeRawPointer.self),toByteOffset:24,as:UnsafeRawPointer.self)
instance.storeBytes(of:UnsafeRawPointer(wt),toByteOffset:32,as:UnsafeRawPointer.self)
let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),format:nil) as! [[String:Any]]
guard let release=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_release") else {fatalError("release missing")}
let releaseObject=unsafeBitCast(release,to:(@convention(c)(UnsafeRawPointer)->Void).self)
var carrierReceipts=[[String:Any]]()
var futures=0,states=[[String:Any]](),delayedCopiesDestroyed=0
for row in input {
 currentMode=row["mode"] as! String
 let source=UnsafeMutablePointer<[String:Any]>.allocate(capacity:1);source.initialize(to:row["input"] as! [String:Any])
 let shell=UnsafeMutableRawPointer.allocate(byteCount:176,alignment:8)
 precondition(invoke(decode,source,nil,nil,shell)==nil);source.deallocate()
 let before=received.count
 let future=owned_swift_scalar(update,shell,nil,nil,nil,instance)
 precondition(future != 0 && received.count==before+1)
 let futurePointer=UnsafeRawPointer(bitPattern:future)!
 let first=owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer)
 precondition(first==(currentMode=="immediate" ? 1:0))
 precondition(invoke(witness(sp,1),shell,sp,nil,nil)==nil);shell.deallocate()
 var second=first
 if currentMode=="delayed" {
  precondition(replyCopy != nil)
  let nativeWire=try PropertyListSerialization.data(fromPropertyList:received.last!,format:.binary,options:0)
  let wire=(row["carrierWire"] as? Data) ?? nativeWire
  let wireObject=wire as NSData
  let receiptPointer=withExtendedLifetime(wireObject) {owned_exchange(Unmanaged.passUnretained(wireObject).toOpaque())!}
  let receiptData=Unmanaged<NSData>.fromOpaque(receiptPointer).takeRetainedValue() as Data
  let receipt=try PropertyListSerialization.propertyList(from:receiptData,format:nil) as! [String:Any]
  precondition(receipt["accepted"] as! Bool)
  carrierReceipts.append(receipt)
  // An SDK acknowledgement does not complete the native Future by itself.
  precondition(owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer)==0)
  owned_reply_unit(sendUnit,replyCopy)
  second=owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer);precondition(second==1)
  precondition(invoke(witness(rp,1),replyCopy,rp,nil,nil)==nil);replyCopy!.deallocate();replyCopy=nil;delayedCopiesDestroyed+=1
 }
 states.append(["mode":currentMode,"successfulBeforeOwnedDelayedReply":first==1,"successfulAfterOwnedDelayedReply":second==1])
 releaseObject(futurePointer);futures+=1
}
instance.deallocate();wt.deinitialize(count:3);wt.deallocate()
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Previews") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let result:[String:Any]=["runtimeImages":runtimeImages,"received":received,"futureReferencesReleased":futures,"calls":received.count,"modernSize":52,"modernStride":56,"modernOffsets":[0,40],"states":states,"carrierReceipts":carrierReceipts,"delayedReplyCopiesDestroyed":delayedCopiesDestroyed]
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("captured",received.count)
