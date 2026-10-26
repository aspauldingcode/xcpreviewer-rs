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
var rows=[[String:Any]](),layouts=[[String:Any]](),destroyedEnums=0,destroyedPlists=0,releasedErrors=0
for kind in ["jit-load-dylib","jit-load-command"] {
 let command=kind=="jit-load-command"
 let prefix=command ? "$s21PreviewsMessagingHost14JITLoadCommandO":"$s21PreviewsMessagingHost14JITLoadCommandO9LoadDylibV"
 let ma=symbol(m,prefix+"Ma",command ? 0x71d40:0x71e94,"PreviewsMessagingHost")
 let metadata=unsafeBitCast(ma,to:Accessor.self)(0),table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 let size=table.load(fromByteOffset:64,as:UInt.self),stride=table.load(fromByteOffset:72,as:UInt.self),alignment=Int((table.load(fromByteOffset:80,as:UInt32.self)&255)+1)
 precondition(metadata.load(as:UInt.self)==(command ? 513:512) && size==40 && stride==40 && alignment==8)
 let decoder=symbol(m,prefix+(command ? "17propertyListValueAC0a10FoundationC008PropertyG0V_tKcfC":"17propertyListValueAE0a10FoundationC008PropertyI0V_tKcfC"),command ? 0x6fefc:0x70658,"PreviewsMessagingHost")
 let encoder=symbol(m,prefix+(command ? "17propertyListValue0a10FoundationC008PropertyG0Vvg":"17propertyListValue0a10FoundationC008PropertyI0Vvg"),command ? 0x6fe28:0x70584,"PreviewsMessagingHost")
 precondition(offset(witness(metadata,1))==0x720b8)
 if !command { for (i,expected) in [0,16,24].enumerated() { precondition(metadata.load(fromByteOffset:16+4*i,as:UInt32.self)==UInt32(expected)) } }
 layouts.append(["kind":kind,"size":size,"stride":stride,"alignment":alignment,"destroyOffset":offset(witness(metadata,1))])
 for item in input where item["kind"] as! String==kind {
  let raw=item["input"] as! [String:Any]
  let source=UnsafeMutablePointer<[String:Any]>.allocate(capacity:1);source.initialize(to:raw)
  let result=UnsafeMutableRawPointer.allocate(byteCount:Int(stride),alignment:alignment)
  let error=invoke(decoder,source,nil,nil,result);source.deallocate()
  if let error=error {errorRelease(error);releasedErrors+=1;result.deallocate();rows.append(["kind":kind,"input":raw,"accepted":false]);continue}
  let plist=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
  precondition(invoke(encoder,nil,nil,result,plist)==nil)
  let canonical=plist.assumingMemoryBound(to:[String:Any].self).pointee
  precondition(invoke(witness(fp,1),plist,fp,nil,nil)==nil);plist.deallocate();destroyedPlists+=1
  precondition(invoke(witness(metadata,1),result,metadata,nil,nil)==nil);result.deallocate();destroyedEnums+=1
  rows.append(["kind":kind,"input":raw,"accepted":true,"canonical":canonical])
 }
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
