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
let f=load("PreviewsFoundationHost"),m=load("PreviewsMessagingHost")
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

final class Monitor {var releases=0}
let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),options:[],format:nil) as! [[String:Any]]
var rows=[[String:Any]](),layouts=[[String:Any]](),destroyedEnums=0,destroyedPlists=0,releasedErrors=0
for kind in ["lazy-property-list"] {
 let ma=symbol(m,"$s21PreviewsMessagingHost16LazyPropertyListOMa",0x6e960,"PreviewsMessagingHost")
 let metadata=unsafeBitCast(ma,to:Accessor.self)(0),table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 let size=table.load(fromByteOffset:64,as:UInt.self),stride=table.load(fromByteOffset:72,as:UInt.self),alignment=Int((table.load(fromByteOffset:80,as:UInt32.self)&255)+1)
 precondition(metadata.load(as:UInt.self)==513 && size==17 && stride==24 && alignment==8)
 layouts.append(["kind":kind,"size":size,"stride":stride,"alignment":alignment,"destroyOffset":offset(witness(metadata,1))])
 if CommandLine.arguments.contains("--metadata-only") { continue }

 precondition(offset(witness(metadata,1))==0x6ef98)
 precondition(MemoryLayout<Data>.size==16 && MemoryLayout<Data>.stride==16 && MemoryLayout<Data>.alignment==8)
 let inject=ma.advanced(by:0x6ea4-0x6e960),tag=ma.advanced(by:0x6ea0-0x6e960)
 let getter=symbol(m,"$s21PreviewsMessagingHost16LazyPropertyListO08propertyF00a10FoundationC00eF0Vvg",0x6e998,"PreviewsMessagingHost")
 let dataGetter=symbol(m,"$s21PreviewsMessagingHost16LazyPropertyListO4data10Foundation4DataVvg",0x6ebfc,"PreviewsMessagingHost")
 for item in input {
  let serialized=item["kind"] as! String=="serialized"
  let original=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
  if serialized {original.assumingMemoryBound(to:Data.self).initialize(to:item["bytes"] as! Data)}
  else {original.assumingMemoryBound(to:[String:Any].self).initialize(to:item["dictionary"] as! [String:Any])}
  precondition(owned_swift_call3(inject,original,UnsafeRawPointer(bitPattern:serialized ? 1:0),metadata,nil,nil)==nil)
  precondition(owned_swift_scalar(tag,original,metadata,nil,nil,nil)==(serialized ? 1:0))
  let copy=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
  precondition(owned_swift_call3(witness(metadata,2),copy,original,metadata,nil,nil)==nil)
  precondition(invoke(witness(metadata,1),original,metadata,nil,nil)==nil);original.deallocate();destroyedEnums+=1
  var row:[String:Any]=["kind":item["kind"]!,"sourceDestroyedBeforeRead":true]
  var decoded=[[String:Any]](),errors=0
  for _ in 0..<2 {
   let result=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
   if let error=invoke(getter,nil,nil,copy,result){errorRelease(error);releasedErrors+=1;errors+=1}
   else {decoded.append(result.assumingMemoryBound(to:[String:Any].self).pointee);precondition(invoke(witness(fp,1),result,fp,nil,nil)==nil);destroyedPlists+=1}
   result.deallocate()
  }
  row["accepted"]=errors==0;row["errorReturns"]=errors;row["decoded"]=decoded
  let dataResult=UnsafeMutablePointer<Data>.allocate(capacity:1)
  if let error=owned_swift_pair(dataGetter,copy,dataResult){errorRelease(error);releasedErrors+=1;row["dataError"]=true}
  else {let bytes=dataResult.move();row["data"]=bytes;row["dataError"]=false}
  dataResult.deallocate()
  precondition(invoke(witness(metadata,1),copy,metadata,nil,nil)==nil);copy.deallocate();destroyedEnums+=1
  rows.append(row)
 }
 // One independently allocated no-copy Data buffer: returned native Data must
 // keep it alive after both enum values are destroyed, then release it once.
 let monitor=Monitor()
 autoreleasepool {
  let original=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
  let buffer=malloc(8192)!;memset(buffer,0x5a,8192)
  original.assumingMemoryBound(to:Data.self).initialize(to:Data(bytesNoCopy:buffer,count:8192,deallocator:.custom {p,n in precondition(n==8192);free(p);monitor.releases+=1}))
  precondition(owned_swift_call3(inject,original,UnsafeRawPointer(bitPattern:1),metadata,nil,nil)==nil)
  let copy=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
  precondition(owned_swift_call3(witness(metadata,2),copy,original,metadata,nil,nil)==nil)
  precondition(invoke(witness(metadata,1),original,metadata,nil,nil)==nil);original.deallocate()
  precondition(monitor.releases==0)
  let returned=UnsafeMutablePointer<Data>.allocate(capacity:1)
  precondition(owned_swift_pair(dataGetter,copy,returned)==nil)
  precondition(invoke(witness(metadata,1),copy,metadata,nil,nil)==nil);copy.deallocate()
  precondition(monitor.releases==0 && returned.pointee.count==8192 && returned.pointee.allSatisfy {$0==0x5a})
  returned.deinitialize(count:1);returned.deallocate()
 }
 precondition(monitor.releases==1)
 rows.append(["kind":"buffer-lifetime","ownedBytes":8192,"aliveAfterSourceAndCopyDestroyed":true,"allReturnedBytesMatched":true,"finalCustomDeallocatorCalls":monitor.releases])

}
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Foundation") && !name.contains("PreviewsMessagingHost") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime image UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let out:[String:Any]=["runtimeImages":runtimeImages,"rows":rows,"layouts":layouts,"destroyedEnums":destroyedEnums,"destroyedPlists":destroyedPlists,"releasedErrors":releasedErrors]
try PropertyListSerialization.data(fromPropertyList:out,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
