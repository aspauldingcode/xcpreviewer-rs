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
let succeeded=symbol(f,"$s22PreviewsFoundationHost6FutureC23hasFinishedSuccessfullySbvg",0xfc348,"PreviewsFoundationHost")
let cm=symbol(f,"$s22PreviewsFoundationHost8CallsiteVMa",0x49998,"PreviewsFoundationHost")
let cp=unsafeBitCast(cm,to:Accessor.self)(0),ct=cp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(cp.load(as:UInt.self)==512 && ct.load(fromByteOffset:64,as:UInt.self)==57 && ct.load(fromByteOffset:72,as:UInt.self)==64 && ct.load(fromByteOffset:80,as:UInt32.self)&255==7)
precondition((0..<4).map{cp.load(fromByteOffset:16+4*$0,as:UInt32.self)}==[0,24,32,40])
let callsiteInit=symbol(f,"$s22PreviewsFoundationHost8CallsiteVyACs12StaticStringV_S2uAEtcfC",0x490ac,"PreviewsFoundationHost")
let makeHandler=symbol(m,"$s21PreviewsMessagingHost14TransportReplyV011makeEncodedE7Handler8callsiteySo14UVPropertyListCSg_s5Error_pSgtc0a10FoundationC08CallsiteV_tF",0x3fb40,"PreviewsMessagingHost")
var currentMode="none",replyCopy:UnsafeMutableRawPointer?=nil
var received=[[String:Any]]()
@_cdecl("owned_transport_record")
func record(_ message:UnsafeRawPointer?,_ reply:UnsafeRawPointer?,_ metadata:UnsafeRawPointer?,_ witnessPointer:UnsafeRawPointer?,_ context:UnsafeRawPointer?) {
 precondition(message != nil && reply != nil && metadata==unsafeBitCast(UInt64.self,to:UnsafeRawPointer.self))
 precondition(context!.load(as:UInt64.self)==0x3132333435363738)
 let raw=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(encode,nil,nil,message,raw)==nil)
 received.append(raw.assumingMemoryBound(to:[String:Any].self).pointee)
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
func field(_ value:Any,_ label:String)->Any {let values=Mirror(reflecting:value).children.filter{$0.label==label};precondition(values.count==1,"qualified field");return values.first!.value}
let stateAccessor=symbol(f,"$s22PreviewsFoundationHost11FutureStateOMa",0xebbf4,"PreviewsFoundationHost")
typealias GenericAccessor=@convention(c)(UInt,UnsafeRawPointer)->UnsafeRawPointer
let stateMetadata=unsafeBitCast(stateAccessor,to:GenericAccessor.self)(0,fp)
let stateTable=stateMetadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
let stateSize=stateTable.load(fromByteOffset:64,as:UInt.self),stateStride=stateTable.load(fromByteOffset:72,as:UInt.self)
fputs("STATE_LAYOUT "+String(stateMetadata.load(as:UInt.self))+" "+String(stateSize)+" "+String(stateStride)+" "+String(stateTable.load(fromByteOffset:80,as:UInt32.self))+"\n",stderr)
if CommandLine.arguments.contains("--metadata-only") {exit(0)}
precondition(stateMetadata.load(as:UInt.self)==513 && stateSize==58 && stateStride==64 && stateTable.load(fromByteOffset:80,as:UInt32.self)&255==7)
let snapshot=symbol(f,"$s22PreviewsFoundationHost6FutureC19recentStateSnapshotAA0dF0OyxGvgTj",0x118b7c,"PreviewsFoundationHost")
var snapshotDispatchOffsets=Set<UInt>()
var snapshotCalls=0,encodedCallbackCalls=0,cancelCalls=0
var cancelDispatchOffsets=Set<UInt>()
func deliver(_ fn:UnsafeMutableRawPointer,_ payload:UnsafeRawPointer?,_ error:UnsafeRawPointer?,_ context:UnsafeRawPointer?,_ result:UnsafeMutableRawPointer?)->UnsafeMutableRawPointer? {
 let returned=invoke(fn,payload,error,context,result);encodedCallbackCalls+=1;return returned
}
func stateValue(_ future:UnsafeRawPointer)->Any {
 snapshotCalls+=1
 let method=future.load(as:UnsafeRawPointer.self).load(fromByteOffset:0x80,as:UnsafeMutableRawPointer.self)
 precondition(offset(method)==0x115868);snapshotDispatchOffsets.insert(offset(method))
 precondition(String(cString:image(method)).hasSuffix("/PreviewsFoundationHost"))
 let storage=UnsafeMutableRawPointer.allocate(byteCount:Int(stateStride),alignment:8)
 precondition(invoke(snapshot,nil,nil,future,storage)==nil)
 let type=unsafeBitCast(stateMetadata,to:Any.Type.self)
 func load<T>(_ type:T.Type)->Any {storage.load(as:T.self)}
 let copy=_openExistential(type,do:load)
 precondition(invoke(witness(stateMetadata,1),storage,stateMetadata,nil,nil)==nil);storage.deallocate()
 return copy
}
func clean(_ text:String)->String {text.replacingOccurrences(of:"\\(unknown context at \\$[0-9a-fA-F]+\\)",with:"(private)",options:.regularExpression)}
func summarize(_ value:Any)->[String:Any] {
 precondition(String(reflecting:type(of:value))=="PreviewsFoundationHost.FutureState<PreviewsFoundationHost.PropertyList>")
 let state=Mirror(reflecting:value);precondition(state.displayStyle == .enum)
 if state.children.isEmpty {precondition(String(describing:value)=="running");return ["state":"running"]}
 let termination=field(value,"finished")
 precondition(String(reflecting:type(of:termination))=="PreviewsFoundationHost.FutureTermination<PreviewsFoundationHost.PropertyList>")
 let children=Array(Mirror(reflecting:termination).children);precondition(children.count==1)
 let result=children[0];precondition(result.label=="succeeded" || result.label=="failed" || result.label=="canceled")
 if result.label=="canceled" {
  precondition(String(reflecting:type(of:result.value))=="PreviewsFoundationHost.Callsite")
  return ["state":"finished","termination":"canceled","callsite":["file":String(describing:field(result.value,"file")),"line":field(result.value,"line") as! UInt,"column":field(result.value,"column") as! UInt,"function":String(describing:field(result.value,"function"))]]
 }
 if result.label=="succeeded" {return ["state":"finished","termination":"succeeded","value":field(result.value,"serializableDictionary") as! [String:Any]]}
 let error=result.value as! Error,native=error as NSError
 var out:[String:Any]=["state":"finished","termination":"failed","errorType":clean(String(reflecting:type(of:error))),"domain":clean(native.domain),"code":native.code,"description":clean(native.localizedDescription),"userInfoKeys":native.userInfo.keys.sorted()]
 if String(reflecting:type(of:error)).hasSuffix(".HumanReadableNSError") {
  let original=field(error,"error") as! NSError
  out["wrappedError"]=["domain":original.domain,"code":original.code,"description":original.localizedDescription]
 }
 return out
}
func cancelNative(_ future:UnsafeRawPointer,_ line:UInt)->[String:Any] {
 let method=future.load(as:UnsafeRawPointer.self).load(fromByteOffset:0xc0,as:UnsafeMutableRawPointer.self)
 fputs("CANCEL_METHOD_OFFSET "+String(offset(method))+"\n",stderr)
 precondition(offset(method)==0x34178 && String(cString:image(method)).hasSuffix("/PreviewsFoundationHost"))
 cancelDispatchOffsets.insert(offset(method))
 let site=UnsafeMutableRawPointer.allocate(byteCount:64,alignment:8)
 owned_callsite_init(callsiteInit,site)
 site.storeBytes(of:line,toByteOffset:24,as:UInt.self)
 precondition(invoke(method,site,nil,future,nil)==nil);cancelCalls+=1
 precondition(invoke(witness(cp,1),site,cp,nil,nil)==nil);site.deallocate()
 return summarize(stateValue(future))
}
var cancellationStates=[[String:Any]]()
var carrierReceipts=[[String:Any]](), repeatedStates=[[String:Any]]()
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
 let beforeSnapshot=summarize(stateValue(futurePointer));precondition(beforeSnapshot["state"] as! String == "running")
 let first=owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer)
 precondition(first==(currentMode=="immediate" ? 1:0))
 precondition(invoke(witness(sp,1),shell,sp,nil,nil)==nil);shell.deallocate()
 var second=first
 if currentMode=="delayed" {
  precondition(replyCopy != nil)
  let callsite=UnsafeMutableRawPointer.allocate(byteCount:64,alignment:8)
  owned_callsite_init(callsiteInit,callsite)
  let pair=UnsafeMutablePointer<UnsafeMutableRawPointer?>.allocate(capacity:2);pair.initialize(repeating:nil,count:2)
  owned_make_handler(makeHandler,callsite,replyCopy,pair)
  precondition(pair[0] != nil && pair[1] != nil && offset(pair[0]!)==0x40114)
  precondition(invoke(witness(cp,1),callsite,cp,nil,nil)==nil);callsite.deallocate()
  precondition(invoke(witness(rp,1),replyCopy,rp,nil,nil)==nil);replyCopy!.deallocate();replyCopy=nil;delayedCopiesDestroyed+=1
  let wire=try PropertyListSerialization.data(fromPropertyList:received.last!,format:.binary,options:0)
  let wireObject=wire as NSData,responseObject=row["responseData"] as! NSData
  var receiptPointer:UnsafeMutableRawPointer?=nil
  let uvPointer=withExtendedLifetime((wireObject,responseObject)) {owned_exchange_uv(Unmanaged.passUnretained(wireObject).toOpaque(),Unmanaged.passUnretained(responseObject).toOpaque(),&receiptPointer)!}
  let receiptData=Unmanaged<NSData>.fromOpaque(receiptPointer!).takeRetainedValue() as Data
  let receipt=try PropertyListSerialization.propertyList(from:receiptData,format:nil) as! [String:Any]
  precondition(receipt["accepted"] as! Bool);carrierReceipts.append(receipt)
  precondition(owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer)==0)
  let uv=Unmanaged<AnyObject>.fromOpaque(uvPointer).takeRetainedValue()
  let error:Error=NSError(domain:"owned.encoded.reply",code:17,userInfo:[NSLocalizedDescriptionKey:"owned reply failure"])
  precondition(MemoryLayout<Error>.size==8)
  let nativeError=unsafeBitCast(error,to:UnsafeRawPointer.self)
  let payload=(row["payloadPresent"] as! Bool) ? UnsafeRawPointer(uvPointer):nil
  let failure=(row["errorPresent"] as! Bool) ? nativeError:nil
  var cancellationSteps=[[String:Any]]()
  if row["cancelOrder"] as! String=="before" {cancellationSteps.append(cancelNative(futurePointer,1));cancellationSteps.append(cancelNative(futurePointer,2))}
  withExtendedLifetime((uv,error)) {precondition(deliver(pair[0]!,payload,failure,pair[1],nil)==nil)}
  let firstResult=summarize(stateValue(futurePointer))
  if row["cancelOrder"] as! String=="after" {cancellationSteps.append(cancelNative(futurePointer,1));cancellationSteps.append(cancelNative(futurePointer,2))}
  cancellationStates.append(["case":row["case"]!,"order":row["cancelOrder"]!,"steps":cancellationSteps])
  fputs("FIRST_CALLBACK_RETURNED "+(row["case"] as! String)+"\n",stderr)
  let laterData=try PropertyListSerialization.data(fromPropertyList:["later":true,"marker":2],format:.binary,options:0) as NSData
  var laterReceipt:UnsafeMutableRawPointer?=nil
  let laterPointer=withExtendedLifetime((wireObject,laterData)) {owned_exchange_uv(Unmanaged.passUnretained(wireObject).toOpaque(),Unmanaged.passUnretained(laterData).toOpaque(),&laterReceipt)!}
  let laterObject=Unmanaged<AnyObject>.fromOpaque(laterPointer).takeRetainedValue()
  let laterReceiptObject=Unmanaged<NSData>.fromOpaque(laterReceipt!).takeRetainedValue()
  let laterReceiptValue=try PropertyListSerialization.propertyList(from:laterReceiptObject as Data,format:nil) as! [String:Any]
  precondition(laterReceiptValue["accepted"] as! Bool);carrierReceipts.append(laterReceiptValue)
  withExtendedLifetime((laterObject,laterReceiptObject)) {precondition(deliver(pair[0]!,UnsafeRawPointer(laterPointer),nil,pair[1],nil)==nil)}
  let afterLaterResult=summarize(stateValue(futurePointer))
  fputs("SECOND_CALLBACK_RETURNED "+(row["case"] as! String)+"\n",stderr)
  withExtendedLifetime((uv,error)) {precondition(deliver(pair[0]!,nil,nil,pair[1],nil)==nil)}
  let afterEmptyResult=summarize(stateValue(futurePointer))
  fputs("THIRD_CALLBACK_RETURNED "+(row["case"] as! String)+"\n",stderr)
  repeatedStates.append(["case":row["case"]!,"first":firstResult,"afterLaterDictionary":afterLaterResult,"afterEmptyReply":afterEmptyResult])
  releaseObject(UnsafeRawPointer(pair[1]!));pair.deinitialize(count:2);pair.deallocate()
  second=owned_swift_scalar(succeeded,nil,nil,nil,nil,futurePointer);precondition(second==((row["expectedSuccess"] as! Bool) && row["cancelOrder"] as! String=="after" ? 1:0))
 }
 let afterSnapshot=summarize(stateValue(futurePointer))
 states.append(["case":row["case"] as! String,"beforeSnapshot":beforeSnapshot,"afterSnapshot":afterSnapshot,"mode":currentMode,"successfulBeforeEncodedCallback":first==1,"successfulAfterEncodedCallback":second==1])
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
let result:[String:Any]=["cancelCalls":cancelCalls,"cancelDispatchOffsets":cancelDispatchOffsets.sorted(),"cancellationStates":cancellationStates,"snapshotCalls":snapshotCalls,"encodedCallbackCalls":encodedCallbackCalls,"runtimeImages":runtimeImages,"received":received,"futureReferencesReleased":futures,"calls":received.count,"snapshotDispatchOffsets":snapshotDispatchOffsets.sorted(),"stateSize":stateSize,"stateStride":stateStride,"modernSize":52,"modernStride":56,"modernOffsets":[0,40],"states":states,"repeatedStates":repeatedStates,"carrierReceipts":carrierReceipts,"delayedReplyCopiesDestroyed":delayedCopiesDestroyed]
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("captured",received.count)
