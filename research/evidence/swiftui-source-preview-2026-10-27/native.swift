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

let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),options:[],format:nil) as! [[String:Any]]
var rows=[[String:Any]](),layouts=[[String:Any]](),destroyedValues=0,destroyedPlists=0,releasedErrors=0
for kind in ["render"] {
 let ma=symbol(m,"$s21PreviewsMessagingHost13RenderPayloadVMa",0x9a6c8,"PreviewsMessagingHost")
 let metadata=unsafeBitCast(ma,to:Accessor.self)(0),table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 let size=table.load(fromByteOffset:64,as:UInt.self),stride=table.load(fromByteOffset:72,as:UInt.self),alignment=Int((table.load(fromByteOffset:80,as:UInt32.self)&255)+1)
 precondition(metadata.load(as:UInt.self)==512 && size==104 && stride==104 && alignment==8)
 let decoder=symbol(m,"$s21PreviewsMessagingHost13RenderPayloadV17propertyListValueAC0a10FoundationC008PropertyG0V_tKcfC",0x8d9a0,"PreviewsMessagingHost")
 let encoder=symbol(m,"$s21PreviewsMessagingHost13RenderPayloadV17propertyListValue0a10FoundationC008PropertyG0Vvg",0x8d740,"PreviewsMessagingHost")
 let offsets=(0..<4).map {metadata.load(fromByteOffset:16+4*$0,as:UInt32.self)}
 layouts.append(["kind":kind,"size":size,"stride":stride,"alignment":alignment,"destroyOffset":offset(witness(metadata,1)),"offsets":offsets])
 if CommandLine.arguments.contains("--metadata-only") { continue }
 precondition(offset(witness(metadata,1))==0x58980 && offsets==[0,80,88,96])


 for item in input where item["kind"] as! String==kind {
  let raw=item["input"] as! [String:Any]
  let source=UnsafeMutablePointer<[String:Any]>.allocate(capacity:1);source.initialize(to:raw)
  let result=UnsafeMutableRawPointer.allocate(byteCount:Int(stride),alignment:alignment)
  fputs("decode \(item["case"]!)\n",stderr);fflush(stderr)
  let error=invoke(decoder,source,nil,nil,result);source.deallocate()
  if let error=error {errorRelease(error);releasedErrors+=1;result.deallocate();rows.append(["case":item["case"]!,"kind":kind,"input":raw,"accepted":false]);continue}
  fputs("decoded \(item["case"]!)\n",stderr);fflush(stderr)
  let plist=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
  precondition(invoke(encoder,nil,nil,result,plist)==nil)
  let canonical=plist.assumingMemoryBound(to:[String:Any].self).pointee
  precondition(invoke(witness(fp,1),plist,fp,nil,nil)==nil);plist.deallocate();destroyedPlists+=1
  precondition(invoke(witness(metadata,1),result,metadata,nil,nil)==nil);result.deallocate();destroyedValues+=1
  rows.append(["case":item["case"]!,"kind":kind,"input":raw,"accepted":true,"canonical":canonical])
  fputs("encoded and destroyed \(item["case"]!)\n",stderr);fflush(stderr)
 }
}
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Foundation") && !name.contains("PreviewsMessagingHost") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime image UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let out:[String:Any]=["runtimeImages":runtimeImages,"rows":rows,"layouts":layouts,"destroyedValues":destroyedValues,"destroyedPlists":destroyedPlists,"releasedErrors":releasedErrors]
try PropertyListSerialization.data(fromPropertyList:out,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
