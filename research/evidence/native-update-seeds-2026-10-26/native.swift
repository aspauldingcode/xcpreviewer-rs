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
let initialize=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxV012propertyListE0AC0a10FoundationC008PropertyH0V_tKcfC",0x1d630,"PreviewsMessagingHost")
let encode=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxV012propertyListE00a10FoundationC008PropertyH0Vvg",0x1d680,"PreviewsMessagingHost")
let required=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxV03getE0xyK0a10FoundationC025PropertyListRepresentableRzlF",0x1d578,"PreviewsMessagingHost")
let optional=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxV011getOptionalE0xSgyK0a10FoundationC025PropertyListRepresentableRzlF",0x1d594,"PreviewsMessagingHost")
let stringWitness=symbol(f,"$sSS22PreviewsFoundationHost25PropertyListRepresentableAAWP",0x18c110,"PreviewsFoundationHost")
let stringMetadata=unsafeBitCast(String.self,to:UnsafeRawPointer.self)
precondition(MemoryLayout<String>.size==16 && MemoryLayout<String?>.size==16)
guard let release=dlsym(UnsafeMutableRawPointer(bitPattern:-2),"swift_errorRelease") else {fatalError("error release unavailable")}
let errorRelease=unsafeBitCast(release,to:(@convention(c)(UnsafeMutableRawPointer)->Void).self)
var counts=["initialized":0,"encoded":0,"destroyedBoxes":0,"destroyedPropertyLists":0,"requiredCalls":0,"optionalCalls":0,"releasedErrors":0]
func make(_ input:[String:Any])->UnsafeMutableRawPointer {
 let source=UnsafeMutablePointer<[String:Any]>.allocate(capacity:1);source.initialize(to:input)
 let result=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 let error=invoke(initialize,UnsafeRawPointer(source),nil,nil,result)
 // initializeWithTake transfers the initialized PropertyList word to the box;
 // deallocate the consumed source buffer without deinitializing its old bits.
 source.deallocate();precondition(error==nil);counts["initialized"]!+=1;return result
}
func destroy(_ box:UnsafeMutableRawPointer) {precondition(invoke(witness(mp,1),box,mp,nil,nil)==nil);counts["destroyedBoxes"]!+=1;box.deallocate()}
func encoded(_ box:UnsafeMutableRawPointer)->[String:Any] {
 let result=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(encode,nil,nil,box,result)==nil)
 // Field0 is the exact Swift Dictionary representation, with the runtime
 // layout checked above. Copy it before native PropertyList destruction.
 let copy=result.assumingMemoryBound(to:[String:Any].self).pointee
 precondition(invoke(witness(fp,1),result,fp,nil,nil)==nil)
 counts["encoded"]!+=1;counts["destroyedPropertyLists"]!+=1;result.deallocate();return copy
}
func stringValue(_ box:UnsafeMutableRawPointer,_ isOptional:Bool)->(Bool,String?) {
 counts[isOptional ? "optionalCalls":"requiredCalls"]!+=1
 if isOptional {
  let result=UnsafeMutablePointer<String?>.allocate(capacity:1)
  let error=invoke(optional,stringMetadata,stringWitness,box,UnsafeMutableRawPointer(result))
  if let error=error {errorRelease(error);counts["releasedErrors"]!+=1;result.deallocate();return (false,nil)}
  let value=result.move();result.deallocate();return (true,value)
 }
 let result=UnsafeMutablePointer<String>.allocate(capacity:1)
 let error=invoke(required,stringMetadata,stringWitness,box,UnsafeMutableRawPointer(result))
 if let error=error {errorRelease(error);counts["releasedErrors"]!+=1;result.deallocate();return (false,nil)}
 let value=result.move();result.deallocate();return (true,value)
}

func scalar(_ fn:UnsafeMutableRawPointer,_ a0:UnsafeRawPointer?,_ a1:UnsafeRawPointer?,_ a2:UnsafeRawPointer?,_ a3:UnsafeRawPointer?,_ context:UnsafeRawPointer?)->UInt {owned_swift_scalar(fn,a0,a1,a2,a3,context)}
let mbase=UnsafeMutableRawPointer(mm).advanced(by:-Int(offset(mm)))
let lazyWitness=mbase.advanced(by:0x20348)
let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])),options:[],format:nil) as! [[String:Any]]
var rows=[[String:Any]](),layouts=[[String:Any]](),destroyedSeeds=0
for kind in ["host-update-seed","host-update-group-seed"] {
 let group=kind=="host-update-group-seed"
 let ma=symbol(m,group ? "$s21PreviewsMessagingHost0C15UpdateGroupSeedVMa":"$s21PreviewsMessagingHost0C10UpdateSeedVMa",group ? 0x27d90:0x27d80,"PreviewsMessagingHost")
 let metadata=unsafeBitCast(ma,to:Accessor.self)(0);verify(metadata)
 let conformance=symbol(m,group ? "$s21PreviewsMessagingHost0C15UpdateGroupSeedV0a10FoundationC025PropertyListRepresentableAAMc":"$s21PreviewsMessagingHost0C10UpdateSeedV0a10FoundationC025PropertyListRepresentableAAMc",group ? 0xb5770:0xb5730,"PreviewsMessagingHost")
 let cache=UnsafeMutablePointer<UInt>.allocate(capacity:1);cache.initialize(to:0)
 let resolved=scalar(lazyWitness,cache,ma,conformance,nil,nil);precondition(resolved != 0 && cache.pointee==resolved);cache.deinitialize(count:1);cache.deallocate()
 let representable=UnsafeRawPointer(bitPattern:resolved)!;precondition(representable.load(as:UnsafeRawPointer.self)==UnsafeRawPointer(conformance))
 let property=symbol(m,group ? "$s21PreviewsMessagingHost0C15UpdateGroupSeedV17propertyListValues6UInt64Vvg":"$s21PreviewsMessagingHost0C10UpdateSeedV17propertyListValues6UInt64Vvg",group ? 0x283b0:0x5ba4,"PreviewsMessagingHost")
 layouts.append(["kind":kind,"size":8,"stride":8,"alignment":8,"valueOffset":metadata.load(fromByteOffset:16,as:UInt32.self)])
 for raw in input {
  let box=make(raw),result=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
  counts["requiredCalls"]!+=1
  let error=invoke(required,metadata,representable,box,result);destroy(box)
  if let error=error {errorRelease(error);counts["releasedErrors"]!+=1;result.deallocate();rows.append(["kind":kind,"input":raw,"accepted":false]);continue}
  let rawValue=result.load(as:UInt64.self)
  let canonical=scalar(property,nil,nil,nil,nil,result);precondition(UInt64(canonical)==rawValue)
  precondition(invoke(witness(metadata,1),result,metadata,nil,nil)==nil);result.deallocate();destroyedSeeds+=1
  rows.append(["kind":kind,"input":raw,"accepted":true,"canonical":UInt64(canonical)])
 }
}
let next=symbol(m,"$s21PreviewsMessagingHost0C10UpdateSeedV4nextACvgZ",0x242dc,"PreviewsMessagingHost")
var sequence=[UInt64]()
for _ in 0..<8 {
 let seed=UnsafeMutablePointer<UInt64>.allocate(capacity:1)
 precondition(invoke(next,nil,nil,nil,UnsafeMutableRawPointer(seed))==nil)
 sequence.append(seed.move());seed.deallocate()
}
let increment=mbase.advanced(by:0x24428)
var increments=[[String:Any]]()
for start in [UInt64(0),UInt64(1),UInt64.max-1,UInt64.max] {
 let source=UnsafeMutablePointer<UInt64>.allocate(capacity:1);source.initialize(to:start)
 let result=UnsafeMutablePointer<UInt64>.allocate(capacity:1)
 precondition(invoke(increment,source,nil,nil,UnsafeMutableRawPointer(result))==nil)
 let value=result.move();result.deallocate();let stored=source.move();source.deallocate();precondition(value==stored)
 increments.append(["before":start,"after":stored,"returned":value])
}
let less=symbol(m,"$s21PreviewsMessagingHost0C15UpdateGroupSeedV1loiySbAC_ACtFZ",0x24594,"PreviewsMessagingHost")
let orderValues=[UInt64(0),UInt64(1),UInt64(Int64.max),UInt64(Int64.max)+1,UInt64.max]
var order=[[String:Any]]()
for a in orderValues {for b in orderValues {
 var left=a,right=b
 let value=withUnsafePointer(to:&left) {l in withUnsafePointer(to:&right) {r in scalar(less,l,r,nil,nil,nil)}}
 precondition(value==0 || value==1);order.append(["left":a,"right":b,"less":value==1])
}}
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Foundation") && !name.contains("PreviewsMessagingHost") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime image UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let output:[String:Any]=["input":input,"rows":rows,"counts":counts,"layouts":layouts,"destroyedSeeds":destroyedSeeds,"nativeNext":sequence,"nativeIncrementClosure":increments,"nativeGroupOrder":order,"runtimeImages":runtimeImages]
try PropertyListSerialization.data(fromPropertyList:output,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
