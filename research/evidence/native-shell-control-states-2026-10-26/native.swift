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
let sm=symbol(m,"$s21PreviewsMessagingHost18ShellUpdatePayloadVMa",0x22930,"PreviewsMessagingHost")
let sp=unsafeBitCast(sm,to:Accessor.self)(0)
let st=sp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
let size=st.load(fromByteOffset:64,as:UInt.self),stride=st.load(fromByteOffset:72,as:UInt.self),alignment=Int((st.load(fromByteOffset:80,as:UInt32.self)&255)+1)
precondition(sp.load(as:UInt.self)==512)
precondition(size==176 && stride==176 && alignment==8)
let decodeShell=symbol(m,"$s21PreviewsMessagingHost18ShellUpdatePayloadV17propertyListValueAC0a10FoundationC008PropertyH0V_tKcfC",0x23570,"PreviewsMessagingHost")
let encodeShell=symbol(m,"$s21PreviewsMessagingHost18ShellUpdatePayloadV17propertyListValue0a10FoundationC008PropertyH0Vvg",0x22df8,"PreviewsMessagingHost")
let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),options:[],format:nil) as! [[String:Any]]
var rows=[[String:Any]](),destroyedShells=0,destroyedPlists=0,releasedShellErrors=0
precondition(offset(witness(sp,1))==0x26ad4)
precondition((0..<11).map {sp.load(fromByteOffset:16+4*$0,as:UInt32.self)}==[0,8,24,40,56,72,88,104,112,120,168])
for raw in input {
 let source=UnsafeMutablePointer<[String:Any]>.allocate(capacity:1);source.initialize(to:raw)
 let result=UnsafeMutableRawPointer.allocate(byteCount:Int(stride),alignment:alignment)
 let error=invoke(decodeShell,source,nil,nil,result);source.deallocate()
 if let error=error {errorRelease(error);releasedShellErrors+=1;result.deallocate();rows.append(["input":raw,"accepted":false]);continue}
 let plist=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(encodeShell,nil,nil,result,plist)==nil)
 let canonical=plist.assumingMemoryBound(to:[String:Any].self).pointee
 precondition(invoke(witness(fp,1),plist,fp,nil,nil)==nil);plist.deallocate();destroyedPlists+=1
 precondition(invoke(witness(sp,1),result,sp,nil,nil)==nil);result.deallocate();destroyedShells+=1
 rows.append(["input":raw,"accepted":true,"canonical":canonical])
}
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Foundation") && !name.contains("PreviewsMessagingHost") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime image UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let out:[String:Any]=["runtimeImages":runtimeImages,"rows":rows,"destroyedShells":destroyedShells,"destroyedPlists":destroyedPlists,"releasedShellErrors":releasedShellErrors,"layout":["size":size,"stride":stride,"alignment":alignment],"destroyOffset":offset(witness(sp,1)),"fieldOffsets":(0..<11).map {sp.load(fromByteOffset:16+4*$0,as:UInt32.self)}]
try PropertyListSerialization.data(fromPropertyList:out,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
