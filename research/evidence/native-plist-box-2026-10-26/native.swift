import Foundation
import Darwin
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
let data=try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))
let inputs=try PropertyListSerialization.propertyList(from:data,options:[],format:nil) as! [[String:Any]]
var rows=[[String:Any]]()
for input in inputs {
 let box=make(input);var row:[String:Any]=["input":input,"encoded":encoded(box)]
 for (key,mode) in [("required",false),("optional",true)] {let (ok,value)=stringValue(box,mode);var state:[String:Any]=["succeeded":ok];if ok {state["isPresent"]=value != nil};if let value=value {state["value"]=value};row[key]=state}
 destroy(box);rows.append(row)
}
let output:[String:Any]=["rows":rows,"counts":counts,"layoutVerified":true,"loadedPinnedModules":true]
try PropertyListSerialization.data(fromPropertyList:output,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("Owned private box init/encoding/required+optional String getters completed; scoped destruction/error releases requested")
