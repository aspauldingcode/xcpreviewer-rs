// Original adapter for the locally qualified macOS26 SwiftUI registry profile.
import SwiftUI
import DeveloperToolsSupport
import Foundation
import Darwin

@available(macOS 14.0, *)
@MainActor enum RegistryBridge {
 static var receipt=[String:Any]()
 enum Failure:Error { case unsupportedRuntime,unsupportedPreviewShape,unsupportedClosure,unexpectedNativeError }
 static func content<P:PreviewRegistry>(_ registry:P.Type) throws -> AnyView {
  var images=[String:String]()
  for i in 0..<owned_image_count() {
   guard let path=owned_image_path(i) else {continue};let name=String(cString:path)
   if !name.contains("DeveloperToolsSupport.framework") && !name.contains("SwiftUI.framework") {continue}
   guard let uuid=owned_image_uuid(i) else {throw Failure.unsupportedRuntime}
   images[name]=(0..<16).map {String(format:"%02x",uuid[$0])}.joined()
  }
  guard Set(images.values)==Set(["5ed60a65de463c51874d608cfced6a11","90f7fa24a2803e8aa62d148b11bfc28d"]),
        MemoryLayout<any View>.size==40,
        let handle=dlopen("/System/Library/Frameworks/SwiftUI.framework/SwiftUI",RTLD_NOW|RTLD_LOCAL),
        let accessor=dlsym(handle,"$s7SwiftUI15ViewPreviewBodyVMa"),
        let getter=dlsym(handle,"$s7SwiftUI15ViewPreviewBodyV4bodyAA0C0_pvg"),
        owned_symbol_offset(accessor)==0x10605b0,owned_symbol_offset(getter)==0x1060458
  else {throw Failure.unsupportedRuntime}
  let metadata=unsafeBitCast(accessor,to:(@convention(c)(UInt)->UnsafeRawPointer).self)(0)
  let table=metadata.load(fromByteOffset:-8,as:UnsafeRawPointer.self)
  let size=table.load(fromByteOffset:64,as:UInt.self),stride=table.load(fromByteOffset:72,as:UInt.self)
  let alignment=Int(table.load(fromByteOffset:80,as:UInt32.self)&255)+1
  let destroy=table.load(fromByteOffset:8,as:UnsafeMutableRawPointer.self)
  guard metadata.load(as:UInt.self)==512,size==40,stride==40,alignment==8,
        metadata.load(fromByteOffset:16,as:UInt32.self)==0,owned_symbol_offset(destroy)==0xc545c,
        String(cString:owned_symbol_path(destroy))==String(cString:owned_symbol_path(getter))
  else {throw Failure.unsupportedRuntime}
  let preview=try P.makePreview()
  guard let traits=Mirror(reflecting:preview).children.first(where:{$0.label=="traits"}),
        Mirror(reflecting:traits.value).children.isEmpty else {throw Failure.unsupportedPreviewShape}
  var cursor:Any=preview
  for label in ["dataSource","preview","structure","singlePreview","makeBody"] {
   guard let next=Mirror(reflecting:cursor).children.first(where:{$0.label==label}) else {throw Failure.unsupportedPreviewShape}
   cursor=next.value
  }
  guard String(reflecting:type(of:cursor))=="@Swift.MainActor () -> SwiftUI.ViewPreviewBody" else {throw Failure.unsupportedClosure}
  func closureInfo<T>(_ value:T) throws -> (UnsafeMutableRawPointer,UnsafeRawPointer?) {
   guard MemoryLayout<T>.size==16,MemoryLayout<T>.alignment==8 else {throw Failure.unsupportedClosure}
   return withUnsafeBytes(of:value) {($0.load(as:UnsafeMutableRawPointer.self),$0.load(fromByteOffset:8,as:UnsafeRawPointer?.self))}
  }
  let closure=try _openExistential(cursor,do:closureInfo)
  guard closure.1 != nil,owned_symbol_offset(closure.0)==0x1060280,
        String(cString:owned_symbol_path(closure.0))==String(cString:owned_symbol_path(getter))
  else {throw Failure.unsupportedClosure}
  return try withExtendedLifetime(cursor) {
   let body=UnsafeMutableRawPointer.allocate(byteCount:40,alignment:8)
   defer {body.deallocate()}
   fputs("Registry capture: invoke body closure\n",stderr);fflush(stderr)
   guard owned_swift_call(closure.0,nil,nil,closure.1,body)==nil else {throw Failure.unexpectedNativeError}
   defer {
    _ = owned_swift_call(destroy,body,metadata,nil,nil)
    receipt["body_destroys"]=1
   }
   let output=UnsafeMutablePointer<any View>.allocate(capacity:1)
   defer {output.deallocate()}
   fputs("Registry capture: invoke body getter\n",stderr);fflush(stderr)
   guard owned_swift_call(getter,nil,nil,body,output)==nil else {throw Failure.unexpectedNativeError}
   let view=output.move()
   receipt=["runtime_images":images,"body_size":40,"body_stride":40,"body_alignment":8,
            "closure_offset":0x1060280,"getter_offset":0x1060458,"destroy_offset":0xc545c,
            "body_calls":1,"getter_calls":1]
   return AnyView(view)
  }
 }
}
