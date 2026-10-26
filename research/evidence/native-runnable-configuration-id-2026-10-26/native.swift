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
// This known nonthrowing shared accessor resolves the exact native conformance.
let conformance=symbol(m,"$s21PreviewsMessagingHost13PlistValueBoxV0a10FoundationC025PropertyListRepresentableAAMc",0xb4690,"PreviewsMessagingHost")
let mbase=UnsafeMutableRawPointer(mm).advanced(by:-Int(offset(mm)))
let lazyWitness=mbase.advanced(by:0x20348)
precondition(offset(lazyWitness)==0x20348)
let cache=UnsafeMutablePointer<UInt>.allocate(capacity:1);cache.initialize(to:0)
let resolved=scalar(lazyWitness,cache,mm,conformance,nil,nil)
precondition(resolved != 0 && cache.pointee==resolved);cache.deinitialize(count:1);cache.deallocate()
let boxWitness=UnsafeRawPointer(bitPattern:resolved)!
precondition(boxWitness.load(as:UnsafeRawPointer.self)==UnsafeRawPointer(conformance))
typealias GenericAccessor=@convention(c)(UInt,UnsafeRawPointer,UnsafeRawPointer)->UnsafeRawPointer
let hma=symbol(f,"$s22PreviewsFoundationHost11HashableBoxVMa",0xab118,"PreviewsFoundationHost")
let hp=unsafeBitCast(hma,to:GenericAccessor.self)(0,mp,boxWitness)
let htable=hp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
let hsize=htable.load(fromByteOffset:64,as:UInt.self)
let hstride=htable.load(fromByteOffset:72,as:UInt.self)
let halign=(htable.load(fromByteOffset:80,as:UInt32.self)&255)+1
let valueOffset=hp.load(fromByteOffset:32,as:UInt32.self)
let snapshotOffset=hp.load(fromByteOffset:36,as:UInt32.self)
precondition(hp.load(as:UInt.self)==512 && hp.load(fromByteOffset:16,as:UnsafeRawPointer.self)==mp && hp.load(fromByteOffset:24,as:UnsafeRawPointer.self)==boxWitness)
precondition(valueOffset==0 && snapshotOffset==8 && hsize==48 && hstride==48 && halign==8 && MemoryLayout<AnyHashable>.size==40)
precondition(offset(witness(hp,1))==0xab454)
let hmake=symbol(f,"$s22PreviewsFoundationHost25PropertyListRepresentablePAAE11hashableBoxAA08HashableH0VyxGvg",0xa9c2c,"PreviewsFoundationHost")
let hget=symbol(f,"$s22PreviewsFoundationHost11HashableBoxV5valuexvg",0x64334,"PreviewsFoundationHost")
let hequal=symbol(f,"$s22PreviewsFoundationHost11HashableBoxV2eeoiySbACyxG_AEtFZ",0xa9b30,"PreviewsFoundationHost")
let hhash=symbol(f,"$s22PreviewsFoundationHost11HashableBoxV9hashValueSivg",0xa9b90,"PreviewsFoundationHost")

let p=load("PreviewsPipeline")
let sm=symbol(p,"$s16PreviewsPipeline18CanvasControlStateVMa",0x461170,"PreviewsPipeline")
let sp=unsafeBitCast(sm,to:Accessor.self)(0)
verify(sp);precondition(offset(witness(sp,1))==0x2734)
let stateInit=symbol(p,"$s16PreviewsPipeline18CanvasControlStateV6statesACSay0A14FoundationHost11HashableBoxVy0a9MessagingH0010PlistValueJ0VGG_tcfC",0x1252a8,"PreviewsPipeline")
let stateEmpty=symbol(p,"$s16PreviewsPipeline18CanvasControlStateV5emptyACvgZ",0x46087c,"PreviewsPipeline")
let stateEqual=symbol(p,"$s16PreviewsPipeline18CanvasControlStateV2eeoiySbAC_ACtFZ",0x46088c,"PreviewsPipeline")
let stateHash=symbol(p,"$s16PreviewsPipeline18CanvasControlStateV9hashValueSivg",0x4609dc,"PreviewsPipeline")
let data=try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))
let input=try PropertyListSerialization.propertyList(from:data,options:[],format:nil) as! [String:Any]
let inputs=input["boxes"] as! [[String:Any]],sequences=input["sequences"] as! [[Int]]
var boxes=[UnsafeMutableRawPointer]()
for value in inputs {
 let original=make(value),result=UnsafeMutableRawPointer.allocate(byteCount:Int(hsize),alignment:Int(halign))
 precondition(invoke(hmake,mp,boxWitness,original,result)==nil);destroy(original);boxes.append(result)
}
let elementType=unsafeBitCast(hp,to:Any.Type.self)
var currentIndices=[Int]()
func makeState<T>(_ type:T.Type)->UnsafeMutableRawPointer {
 precondition(MemoryLayout<T>.size==48 && MemoryLayout<T>.stride==48 && MemoryLayout<T>.alignment==8 && MemoryLayout<[T]>.size==8)
 let values=currentIndices.map {boxes[$0].assumingMemoryBound(to:T.self).pointee}
 let owner=UnsafeMutablePointer<[T]>.allocate(capacity:1);owner.initialize(to:values)
 let arrayWord=UnsafeRawPointer(owner).load(as:UnsafeRawPointer.self)
 let result=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(stateInit,arrayWord,nil,nil,result)==nil)
 // Native init transfers the owned Array word; its consumed temporary must not
 // deinitialize. The independent Swift values Array releases its own copy.
 owner.deallocate();return result
}
var states=[UnsafeMutableRawPointer]()
for sequence in sequences {currentIndices=sequence;states.append(_openExistential(elementType,do:makeState))}
let empty=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
precondition(invoke(stateEmpty,nil,nil,nil,empty)==nil);states.append(empty)
// All native states now own independent element copies. Destroy original pool
// wrappers before reading/comparing any state values.
for box in boxes {precondition(invoke(witness(hp,1),box,hp,nil,nil)==nil);box.deallocate()}

func call3(_ fn:UnsafeMutableRawPointer,_ a0:UnsafeRawPointer?,_ a1:UnsafeRawPointer?,_ a2:UnsafeRawPointer?,_ context:UnsafeRawPointer?,_ out:UnsafeMutableRawPointer?)->UnsafeMutableRawPointer? {owned_swift_call3(fn,a0,a1,a2,context,out)}
let cm=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationVMa",0x3c1058,"PreviewsPipeline")
let im=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationV2IDVMa",0x3c1168,"PreviewsPipeline")
let cp=unsafeBitCast(cm,to:Accessor.self)(0),ip=unsafeBitCast(im,to:Accessor.self)(0)
for metadata in [cp,ip] {
 let table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
 precondition(metadata.load(as:UInt.self)==512 && table.load(fromByteOffset:64,as:UInt.self)==24 && table.load(fromByteOffset:72,as:UInt.self)==24 && table.load(fromByteOffset:80,as:UInt32.self)&255==7)
 precondition((0..<3).map {metadata.load(fromByteOffset:16+4*$0,as:UInt32.self)}==[0,8,16])
 precondition(offset(witness(metadata,1))==0x3c5b68)
}
let configInit=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationV11displayMode9overrides12controlStateAeA0c7DisplayG0O_Say0A13MessagingHost0C7VariantVGAA013CanvasControlJ0VtcfC",0x3a4d50,"PreviewsPipeline")
let getID=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationV2idAE2IDVvg",0x3b9d1c,"PreviewsPipeline")
let idEqual=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationV2IDV2eeoiySbAG_AGtFZ",0x3b9a40,"PreviewsPipeline")
let idHash=symbol(p,"$s16PreviewsPipeline15PreviewRunnableV13ConfigurationV2IDV9hashValueSivg",0x3b9c7c,"PreviewsPipeline")
let vm=symbol(m,"$s21PreviewsMessagingHost14PreviewVariantVMa",0xa4930,"PreviewsMessagingHost")
let vdm=symbol(m,"$s21PreviewsMessagingHost14PreviewVariantV2IDVMa",0xa4940,"PreviewsMessagingHost")
let vp=unsafeBitCast(vm,to:Accessor.self)(0),vdp=unsafeBitCast(vdm,to:Accessor.self)(0)
let vtable=vp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
let vsize=vtable.load(fromByteOffset:64,as:UInt.self),vstride=vtable.load(fromByteOffset:72,as:UInt.self)
let valign=Int((vtable.load(fromByteOffset:80,as:UInt32.self)&255)+1)
let vdtable=vdp.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
precondition(vdp.load(as:UInt.self)==512 && vdp.load(fromByteOffset:16,as:UInt32.self)==0 && vdtable.load(fromByteOffset:64,as:UInt.self)==16 && vdtable.load(fromByteOffset:72,as:UInt.self)==16 && vdtable.load(fromByteOffset:80,as:UInt32.self)&255==7)
let vconformance=symbol(m,"$s21PreviewsMessagingHost14PreviewVariantV0a10FoundationC025PropertyListRepresentableAAMc",0xc17f8,"PreviewsMessagingHost")
let vcache=UnsafeMutablePointer<UInt>.allocate(capacity:1);vcache.initialize(to:0)
let vw=scalar(lazyWitness,vcache,vm,vconformance,nil,nil)
precondition(vw != 0 && vcache.pointee==vw);vcache.deinitialize(count:1);vcache.deallocate()
let variantWitness=UnsafeRawPointer(bitPattern:vw)!
precondition(variantWitness.load(as:UnsafeRawPointer.self)==UnsafeRawPointer(vconformance))
let variantEncode=symbol(m,"$s21PreviewsMessagingHost14PreviewVariantV17propertyListValue0a10FoundationC008PropertyG0Vvg",0xa17bc,"PreviewsMessagingHost")
let variantsInput=input["variants"] as! [[String:Any]],cases=input["configurations"] as! [[String:Any]]
var variants=[UnsafeMutableRawPointer](),variantRows=[[String:Any]]()
for raw in variantsInput {
 let source=make(["value":raw]),value=UnsafeMutableRawPointer.allocate(byteCount:Int(vstride),alignment:valign)
 let error=invoke(required,vp,variantWitness,source,value)
 destroy(source)
 if let error=error {errorRelease(error);value.deallocate();fputs("Typed native PreviewVariant decode failed\n",stderr);exit(2)}
 let plist=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(invoke(variantEncode,nil,nil,value,plist)==nil)
 let canonical=plist.assumingMemoryBound(to:[String:Any].self).pointee
 precondition(invoke(witness(fp,1),plist,fp,nil,nil)==nil);plist.deallocate()
 variantRows.append(["input":raw,"canonical":canonical]);variants.append(value)
}
let variantType=unsafeBitCast(vp,to:Any.Type.self),variantIDType=unsafeBitCast(vdp,to:Any.Type.self)
var currentCase=[String:Any]()
func makeConfiguration<T>(_ type:T.Type)->UnsafeMutableRawPointer {
 precondition(MemoryLayout<T>.size==Int(vsize) && MemoryLayout<T>.stride==Int(vstride) && MemoryLayout<T>.alignment==valign)
 let indices=currentCase["overrides"] as! [Int]
 let values=indices.map {variants[$0].assumingMemoryBound(to:T.self).pointee}
 let owner=UnsafeMutablePointer<[T]>.allocate(capacity:1);owner.initialize(to:values)
 let arrayWord=UnsafeRawPointer(owner).load(as:UnsafeRawPointer.self)
 let state=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
 precondition(call3(witness(sp,2),state,states[currentCase["state"] as! Int],sp,nil,nil)==nil)
 var mode=UInt8(currentCase["mode"] as! Int)
 let result=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
 withUnsafePointer(to:&mode) {address in precondition(call3(configInit,address,arrayWord,state,nil,result)==nil)}
 owner.deallocate();state.deallocate();return result
}
var ids=[UnsafeMutableRawPointer]()
for row in cases {
 currentCase=row;let configuration=_openExistential(variantType,do:makeConfiguration)
 let id=UnsafeMutableRawPointer.allocate(byteCount:24,alignment:8)
 precondition(invoke(getID,nil,nil,configuration,id)==nil)
 precondition(invoke(witness(cp,1),configuration,cp,nil,nil)==nil);configuration.deallocate();ids.append(id)
}
// IDs must survive destruction of configurations and both source pools.
for value in variants {precondition(invoke(witness(vp,1),value,vp,nil,nil)==nil);value.deallocate()}
for state in states {precondition(invoke(witness(sp,1),state,sp,nil,nil)==nil);state.deallocate()}
var currentID:UnsafeRawPointer=UnsafeRawPointer(ids[0])
func readOverrideIDs<T>(_ type:T.Type)->[String] {
 precondition(MemoryLayout<T>.size==16 && MemoryLayout<T>.stride==16 && MemoryLayout<T>.alignment==8)
 let values=currentID.advanced(by:8).assumingMemoryBound(to:[T].self).pointee
 return values.map {value in withUnsafePointer(to:value) {$0.withMemoryRebound(to:String.self,capacity:1) {$0.pointee}}}
}
var currentState:UnsafeRawPointer=UnsafeRawPointer(ids[0]).advanced(by:16)
func readState<T>(_ type:T.Type)->[[String:Any]] {
 let values=currentState.assumingMemoryBound(to:[T].self).pointee
 return values.map {element in
  withUnsafePointer(to:element) {address in
   let copy=UnsafeMutableRawPointer.allocate(byteCount:8,alignment:8)
   precondition(invoke(hget,hp,nil,address,copy)==nil)
   let value=encoded(copy);destroy(copy);return value
  }
 }
}

var rows=[[String:Any]](),hashes=[UInt]()
for id in ids {
 currentID=UnsafeRawPointer(id);currentState=currentID.advanced(by:16)
 let overrideIDs=_openExistential(variantIDType,do:readOverrideIDs)
 let controls=_openExistential(elementType,do:readState)
 rows.append(["mode":Int(id.load(as:UInt8.self)),"overrideIDs":overrideIDs,"controlState":controls])
 hashes.append(scalar(idHash,nil,nil,nil,nil,id))
}
var pairs=[[String:Any]]()
for i in ids.indices {for j in ids.indices {
 let equal=scalar(idEqual,ids[i],ids[j],nil,nil,nil);precondition(equal==0 || equal==1)
 if equal==1 {precondition(hashes[i]==hashes[j])}
 pairs.append(["left":i,"right":j,"equal":equal==1,"sameHash":hashes[i]==hashes[j]])
}}
for id in ids {precondition(invoke(witness(ip,1),id,ip,nil,nil)==nil);id.deallocate()}
var runtimeImages=[String:String]()
for i in 0..<owned_image_count() {
 guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
 if !name.contains("Foundation") && !name.contains("PreviewsPipeline") && !name.contains("libswiftCore.") {continue}
 guard let uuid=owned_image_uuid(i) else {fatalError("runtime image UUID unavailable")}
 runtimeImages[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
}
let output:[String:Any]=["input":input,"variants":variantRows,"rows":rows,"pairs":pairs,"counts":counts,"nativeConfigurationCount":ids.count,"nativeConfigurationDestructionReturns":ids.count,"nativeIDDestructionReturns":ids.count,"sourceVariantDestructionReturns":variants.count,"sourceStateDestructionReturns":states.count,"sourceWrapperDestructionReturns":boxes.count,"runtimeImages":runtimeImages,"privateRunnableConfigurationIDMethodsInvoked":true,"variantLayout":["size":vsize,"stride":vstride,"alignment":valign]]
try PropertyListSerialization.data(fromPropertyList:output,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("Native runnable Configuration init/id/equality/hash/copies/destruction and typed PreviewVariant decoder/encoder completed")
